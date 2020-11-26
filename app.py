import datetime
import constants
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from models import (Documento, Titulo, Movimento)

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

modes = {'contas_a_pagar': 'pagar', 'contas_a_receber': 'receber'}

# Documentos
@app.route('/api/v1/documentos', methods=['GET'])
def get_documentos():
    documentos = []
    result = Documento.query.all
    for documento in result:
        documentos.append(documento.serialize)
    return jsonify(documentos)

@app.route('/api/v1/documentos/<id>', methods=['GET'])
def get_documento(id):
    try:
        documento = Documento.query.filter_by(id=id).first()
        return jsonify({'documento': documento.serialize})
    except:
        return not_found("Documento does not exist.")

@app.route('/api/v1/documentos', methods=['POST'])
def create_documento():
    request_json = request.get_json()
    field_validation_error = validate_json_request_and_required_fields(request, Documento.required_fields)
    if field_validation_error is not None:
        return field_validation_error
    documento = Documento(
        id_externo=request_json['id_externo'],
        descricao=request_json['descricao']
    )
    db.session.add(documento)
    db.session.commit()
    return jsonify({'documento': documento.serialize}), 201

# Titulos
@app.route('/api/v1/<mode>/titulos', methods=['GET'])
def get_titulos(mode):
    if mode not in modes:
        return not_found('Mode not found')
    titulos = []
    result = Titulo.query.filter_by(tipo=modes[mode])
    for titulo in result:
        titulos.append(titulo.serialize)
    return jsonify(titulos)

@app.route('/api/v1/<mode>/titulos/<id>', methods=['GET'])
def get_titulo(mode, id):
    if mode not in modes:
        return not_found('Mode not found')
    try:
        titulo = Titulo.query.filter_by(id=id, tipo=modes[mode]).first_or_404()
        return jsonify({'titulo': titulo.serialize})
    except:
        return not_found("Titulo does not exist.")

@app.route('/api/v1/<mode>/titulos', methods=['POST'])
def create_titulo(mode):
    if mode not in modes:
        return not_found('Mode not found')
    request_json = request.get_json()
    field_validation_error = validate_json_request_and_required_fields(request, Titulo.required_fields)
    if field_validation_error is not None:
        return field_validation_error

    try:
        data_vencimento = datetime.datetime.strptime(request_json['data_vencimento'], constants.DATE_FORMAT)
    except:
        return bad_request('Incorrect date format for data_vencimento.')
    try:
        titulo = Titulo(
            id_externo=request_json['id_externo'],
            id_documento=request_json['id_documento'],
            beneficiario=request_json['beneficiario'],
            valor=request_json['valor'],
            data_vencimento=data_vencimento,
            tipo=modes[mode],
            valor_desconto=request_json.get('valor_desconto'),
            valor_juro=request_json.get('valor_juro'),
            valor_multa=request_json.get('valor_multa')          
        )

        db.session.add(titulo)
        db.session.commit()

        movimento = Movimento(
            id_titulo=titulo.id, 
            valor_movimentado=titulo.valor_aberto + titulo.valor_multa + titulo.valor_juro,
            tipo='abertura'
        )

        db.session.add(movimento)
        db.session.commit()
    except:
        return bad_request('Given id_documento does not exist.')
    return jsonify({'titulo': titulo.serialize}), 201

@app.route('/api/v1/<mode>/titulos/<id>/cancel', methods=['POST'])
def cancel_titulo(mode, id):
    if mode not in modes:
        return not_found('Mode not found')
    try:
        titulo: Titulo   
        movimento: Movimento

        titulo = Titulo.query.filter_by(id=id, tipo=modes[mode]).first_or_404()

        movimento = Movimento(
            id_titulo=titulo.id,
            valor_movimentado=titulo.valor_aberto,
            tipo='cancelamento'
        )

        titulo.situacao = 'cancelado'
        titulo.valor_aberto = 0

        db.session.add(movimento)
        db.session.merge(titulo)
        db.session.commit()

        return jsonify({'titulo': titulo.serialize})
    except:
        return not_found("Titulo does not exist.")

@app.route('/api/v1/<mode>/titulos/<id>/substitute', methods=['POST'])
def substitute_titulo(mode, id):
    if mode not in modes:
        return not_found('Mode not found')
    try:
        request_json = request.get_json()
        validate_json_request_and_required_fields(request, ['id_substituido_por'])

        titulo: Titulo
        movimento: Movimento

        titulo = Titulo.query.filter_by(id=id, tipo=modes[mode]).first_or_404()

        movimento = Movimento(
            id_titulo=titulo.id, 
            valor_movimentado=titulo.valor_aberto,
            tipo='substituição'
        )

        titulo.situacao = 'substituido'
        titulo.valor_aberto = 0
        titulo.id_substituido_por = request_json['id_substituido_por']

        db.session.add(movimento)
        db.session.merge(titulo)
        db.session.commit()

        return jsonify({'titulo': titulo.serialize})
    except:
        return not_found("Titulo does not exist.")

@app.route('/api/v1/<mode>/titulos/<id>/liquidate', methods=['POST'])
def liquidate_titulo(mode, id):
    if mode not in modes:
        return not_found('Mode not found')
    try:
        titulo: Titulo
        movimento: Movimento

        titulo = Titulo.query.filter_by(id=id, tipo=modes[mode]).first_or_404()

        if titulo.situacao == 'liquidado':
            return bad_request('Titulo is already liquidated.')

        movimento = Movimento(
            id_titulo=titulo.id, 
            valor_movimentado=titulo.valor_aberto + titulo.valor_multa + titulo.valor_juro,
            tipo='liquidação total'
        )

        titulo.situacao = 'liquidado'
        titulo.valor_aberto = 0
        titulo.valor_multa = 0
        titulo.valor_juro = 0

        db.session.add(movimento)
        db.session.merge(titulo)
        db.session.commit()

        return jsonify({'titulo': titulo.serialize})
    except:
        return not_found("Titulo does not exist.")

@app.route('/api/v1/<mode>/titulos/<id>/pay', methods=['POST'])
def pay_bill(mode, id):
    if mode not in modes:
        return not_found('Mode not found')
    try:
        request_json = request.get_json()
        validate_json_request_and_required_fields(request, ['valor'])

        titulo: Titulo 
        movimento: Movimento

        titulo = Titulo.query.filter_by(id=id, tipo=modes[mode]).first_or_404()

        if request_json['valor'] >= titulo.valor_aberto:
            return bad_request('Amount given is greater or equal to bill amount.')
        
        movimento = Movimento(
            id_titulo=titulo.id,
            valor_movimentado=request_json['valor'],
            tipo='liquidação parcial'
        )

        db.session.add(movimento)
        db.session.commit()
        titulo.valor_aberto -= movimento.valor_movimentado

        db.session.merge(titulo)
        db.session.commit()

        return jsonify({'titulo': titulo.serialize})
    except:
        return not_found("Titulo does not exist.")

@app.route('/api/v1/<mode>/titulos/<id>/pay_by_card', methods=['POST'])
def pay_bill_by_card(mode, id):
    if mode not in modes:
        return not_found('Mode not found')
    try:
        request_json = request.get_json()
        validate_json_request_and_required_fields(request, ['beneficiario'])

        titulo: Titulo
        movimento: Movimento

        titulo = Titulo.query.filter_by(id=id, tipo=modes[mode]).first_or_404()

        new_titulo = Titulo(
            id_documento = titulo.id_documento,
            id_externo=titulo.id_externo,
            valor=titulo.valor_original,
            valor_desconto=titulo.valor_desconto,
            valor_juro=titulo.valor_juro,
            valor_multa=titulo.valor_multa,    
            beneficiario=request_json['beneficiario'],
            situacao='aberto',
            tipo=modes[mode],
            data_vencimento=titulo.data_vencimento
        )

        movimento = Movimento(
            id_titulo=titulo.id, 
            valor_movimentado=titulo.valor_aberto,
            tipo='substituição'
        )

        db.session.add(movimento)
        db.session.add(new_titulo)
        db.session.commit()

        new_movimento = Movimento(
            id_titulo=new_titulo.id, 
            valor_movimentado=new_titulo.valor_aberto + new_titulo.valor_multa + new_titulo.valor_juro,
            tipo='abertura'
        )

        titulo.id_substituido_por = new_titulo.id
        titulo.situacao = 'substituido'
        titulo.valor_aberto = 0

        db.session.add(new_movimento)
        db.session.merge(titulo)
        db.session.commit()

        return jsonify({'titulo': new_titulo.serialize})
    except:
        return not_found("Titulo does not exist.")
    
def validate_json_request_and_required_fields(request: request, required_fields: list):
    request_json = request.get_json()
    if not request.is_json:
        return bad_request('Request is not json.')
    for field in required_fields:
        if field not in list(request_json.keys()):
            return bad_request('Missing required data (' + field + ').')

def bad_request(message):
    response = jsonify({'error': message})
    response.status_code = 400
    return response

def not_found(message):
    response = jsonify({'error': message})
    response.status_code = 404
    return response

if __name__ == '__main__':
    app.run(debug=True)
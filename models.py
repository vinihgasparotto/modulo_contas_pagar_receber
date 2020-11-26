import constants
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime
db = SQLAlchemy()

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_externo = db.Column(db.Text, nullable=True)
    descricao = db.Column(db.Text, nullable=True)

    titulos = db.relationship('Titulo', backref='documento', lazy='select')

    required_fields = {'descricao'}

    def __init__(self, **kwargs):
        self.id_externo = kwargs['id_externo']
        self.descricao = kwargs['descricao']
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'id_externo': self.id_externo,
            'descricao': self.descricao,
            'titulos': [titulo.serialize for titulo in self.titulos]
        }

class Titulo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_externo = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.Text, nullable=False)
    beneficiario = db.Column(db.Text, nullable=False)
    valor_original = db.Column(db.Float, nullable=False)
    valor_aberto = db.Column(db.Float, nullable=False)
    valor_juro = db.Column(db.Float, nullable=True)
    valor_multa = db.Column(db.Float, nullable=True)
    valor_desconto = db.Column(db.Float, nullable=True)
    situacao = db.Column(db.Text, nullable=False)
    data_vencimento = db.Column(db.Text, nullable=False)

    id_documento = db.Column(db.Integer, db.ForeignKey('documento.id'), nullable=True)
    id_substituido_por = db.Column(db.Integer, db.ForeignKey('titulo.id'), nullable=True)

    movimentos = db.relationship('Movimento', backref='bill', lazy='select')

    required_fields = {'id_documento', 'id_externo', 'beneficiario', 'valor', 'data_vencimento'}

    def __init__(self, **kwargs):
        self.id_externo = kwargs['id_externo']
        self.beneficiario = kwargs['beneficiario']
        self.valor_desconto = kwargs.get('valor_desconto') or 0
        self.valor_aberto = kwargs['valor'] - self.valor_desconto
        self.valor_original = kwargs['valor']
        self.id_documento = kwargs['id_documento']
        self.situacao = 'aberto'
        self.tipo = kwargs['tipo']
        self.data_vencimento = kwargs['data_vencimento']
        self.valor_juro = kwargs.get('valor_juro') or 0
        self.valor_multa = kwargs.get('valor_multa') or 0

    @property
    def serialize(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'beneficiario': self.beneficiario,
            'valor_aberto': self.valor_aberto,
            'valor_original': self.valor_original,
            'valor_juro': self.valor_juro,
            'valor_multa': self.valor_multa,
            'valor_desconto': self.valor_desconto,
            'situacao': self.situacao, 
            'data_vencimento': self.data_vencimento.strftime(constants.DATE_FORMAT),
            'id_documento': self.id_documento,
            'id_substituido_por:': self.id_substituido_por,
            'movimentos': [movimento.serialize for movimento in self.movimentos]
        }

class Movimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor_movimentado = db.Column(db.Float, nullable=False)
    juro_movimentado = db.Column(db.Float, nullable=False)
    multa_movimentada = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.Text, nullable=False)
    data_movimento = db.Column(db.Text, nullable=False)

    id_titulo = db.Column(db.Integer, db.ForeignKey('titulo.id'), nullable=False)

    required_fields = {'id_titulo', 'valor_movimentado', 'tipo'}

    def __init__(self, **kwargs):
        self.id_titulo = kwargs['id_titulo']
        self.valor_movimentado = kwargs['valor_movimentado']
        self.juro_movimentado = kwargs.get('juro_movimentado') or 0
        self.multa_movimentada = kwargs.get('multa_movimentada') or 0
        self.tipo = kwargs['tipo']
        self.data_movimento = kwargs.get('data_movimento') or datetime.datetime.now().strftime(constants.DATETIME_FORMAT)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'valor_movimentado': self.valor_movimentado,
            'juro_movimentado': self.juro_movimentado,
            'multa_movimentada': self.multa_movimentada,
            'tipo': self.tipo,
            'data_movimento': self.data_movimento.strftime(constants.DATETIME_FORMAT),
            'id_titulo': self.id_titulo
        }
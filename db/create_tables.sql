CREATE TABLE IF NOT EXISTS documento (
	id serial PRIMARY KEY,
	id_externo text NOT NULL,
	descricao text NOT NULL
);

CREATE TABLE IF NOT EXISTS titulo (
	id serial PRIMARY KEY,
    id_externo text NOT NULL,
    beneficiario text NOT NULL,
    situacao text NOT NULL,
    tipo text NOT NULL,
    valor_original float NOT NULL,
    valor_aberto float NOT NULL,
    valor_juro float NULL,
    valor_multa float NULL,
    valor_desconto float NULL,
    data_vencimento date NOT NULL,
    id_documento integer NOT NULL,
    id_substituido_por integer NULL,
    FOREIGN KEY (id_documento) REFERENCES documento (id),
    FOREIGN KEY (id_substituido_por) REFERENCES titulo (id)
);

CREATE TABLE IF NOT EXISTS movimento (
	id serial PRIMARY KEY,
    valor_movimentado float NOT NULL,
    juro_movimentado float NOT NULL,
    multa_movimentada float NOT NULL,
    tipo text NOT NULL,
    data_movimento timestamp NOT NULL,
    id_titulo integer NULL,
    FOREIGN KEY (id_titulo) REFERENCES titulo (id)
);
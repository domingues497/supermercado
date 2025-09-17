from datetime import datetime
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates
from sqlalchemy import event, CheckConstraint, UniqueConstraint
from app import db
from app.utils import validar_cpf

class Produto(db.Model):
    __tablename__ = "produto"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco_unit = db.Column(db.Numeric(10, 2), nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)
    imagem = db.Column(db.String(200))  # <-- novo campo

    criado_em = db.Column(db.DateTime, default=db.func.now())
    atualizado_em = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    __table_args__ = (
        CheckConstraint('estoque >= 0', name='check_estoque_non_negative'),
    )

    def __repr__(self):
        return f'<Produto {self.nome}>'

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)  # <-- novo
    criado_em = db.Column(db.DateTime, server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=db.func.now())

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Venda(db.Model):
    __tablename__ = 'venda'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref='vendas')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False)

class VendaItem(db.Model):
    __tablename__ = 'venda_item'

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id', ondelete='CASCADE'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unit = db.Column(db.Numeric(10, 2), nullable=False)

    venda = db.relationship('Venda', backref='itens')
    produto = db.relationship('Produto')

    __table_args__ = (
        CheckConstraint('quantidade > 0', name='check_quantidade_positive'),
    )

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(140), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def get_id(self):
        return str(self.id)

    @validates('email')
    def validate_email(self, key, email):
        import re
        if not re.match(r'^[\w\.-]+@mercado\.com\.br$', email):
            raise ValueError('Email deve ser do domínio mercado.com.br')
        return email

# ----------- EVENTS (VALIDAÇÕES / INTEGRIDADE) -----------

@event.listens_for(Cliente, 'before_update')
def impedir_alteracao_cpf(mapper, connection, target):
    estado = db.inspect(target)
    hist = estado.attrs.cpf.history
    if hist.has_changes():
        raise ValueError('CPF não pode ser alterado.')

@event.listens_for(Cliente, 'before_insert')
@event.listens_for(Cliente, 'before_update')
def validar_cpf_cliente(mapper, connection, target):
    cpf = ''.join(filter(str.isdigit, target.cpf))
    if not validar_cpf(cpf):
        raise ValueError('CPF inválido.')
    target.cpf = cpf

@event.listens_for(Produto, 'before_delete')
def impedir_exclusao_produto_se_vendido(mapper, connection, target):
    venda_item = db.session.query(VendaItem).filter_by(produto_id=target.id).first()
    if venda_item:
        raise ValueError('Produto não pode ser excluído: já utilizado em venda.')

@event.listens_for(Cliente, 'before_delete')
def impedir_exclusao_cliente_com_vendas(mapper, connection, target):
    venda = db.session.query(Venda).filter_by(cliente_id=target.id).first()
    if venda:
        raise ValueError('Cliente não pode ser excluído: possui vendas registradas.')

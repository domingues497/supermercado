from flask import Blueprint, request, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
from app.models import db, Produto, Cliente, Venda, VendaItem, AdminUser
from app.utils import validar_cpf
from decimal import Decimal

bp = Blueprint('api', __name__)
auth = HTTPBasicAuth()

# ------------------- AUTH ADMIN -------------------

@auth.verify_password
def verify_password(email, senha):
    admin = AdminUser.query.filter_by(email=email).first()
    if admin and check_password_hash(admin.senha_hash, senha):
        return admin

# ------------------- UTIL -------------------

def response(data=None, error=False, message='', fields=None, code=200):
    return jsonify({
        'data': data,
        'error': error,
        'message': message,
        'fields': fields or {}
    }), code

# ------------------- PRODUTOS -------------------

@bp.route('/produtos', methods=['GET'])
@auth.login_required
def api_listar_produtos():
    termo = request.args.get('search', '')
    produtos = Produto.query.filter(
        Produto.nome.ilike(f'%{termo}%')
    ).all()
    data = [{
        'id': p.id,
        'nome': p.nome,
        'descricao': p.descricao,
        'preco_unit': str(p.preco_unit),
        'estoque': p.estoque
    } for p in produtos]
    return response(data=data)

@bp.route('/produtos', methods=['POST'])
@auth.login_required
def api_criar_produto():
    dados = request.json
    try:
        produto = Produto(
            nome=dados['nome'],
            descricao=dados['descricao'],
            preco_unit=Decimal(dados['preco_unit']),
            estoque=dados['estoque']
        )
        db.session.add(produto)
        db.session.commit()
        return response(data={'id': produto.id}, message='Produto criado.', code=201)
    except Exception as e:
        db.session.rollback()
        return response(error=True, message=str(e), code=400)

@bp.route('/produtos/<int:id>', methods=['GET'])
@auth.login_required
def api_get_produto(id):
    produto = Produto.query.get_or_404(id)
    data = {
        'id': produto.id,
        'nome': produto.nome,
        'descricao': produto.descricao,
        'preco_unit': str(produto.preco_unit),
        'estoque': produto.estoque
    }
    return response(data=data)

@bp.route('/produtos/<int:id>', methods=['PUT'])
@auth.login_required
def api_update_produto(id):
    produto = Produto.query.get_or_404(id)
    dados = request.json
    try:
        produto.nome = dados['nome']
        produto.descricao = dados['descricao']
        produto.preco_unit = Decimal(dados['preco_unit'])
        produto.estoque = dados['estoque']
        db.session.commit()
        return response(message='Produto atualizado.')
    except Exception as e:
        db.session.rollback()
        return response(error=True, message=str(e), code=400)

@bp.route('/produtos/<int:id>', methods=['DELETE'])
@auth.login_required
def api_delete_produto(id):
    produto = Produto.query.get_or_404(id)
    try:
        db.session.delete(produto)
        db.session.commit()
        return response(message='Produto excluído.')
    except:
        db.session.rollback()
        return response(error=True, message='Produto vinculado a venda.', code=409)

# ------------------- CLIENTES -------------------

@bp.route('/clientes', methods=['GET'])
@auth.login_required
def api_listar_clientes():
    clientes = Cliente.query.all()
    data = [{
        'id': c.id,
        'nome': c.nome,
        'cpf': c.cpf
    } for c in clientes]
    return response(data=data)

@bp.route('/clientes', methods=['POST'])
@auth.login_required
def api_criar_cliente():
    dados = request.json
    cpf = ''.join(filter(str.isdigit, dados['cpf']))
    if not validar_cpf(cpf):
        return response(error=True, message='CPF inválido.', code=422)

    try:
        cliente = Cliente(nome=dados['nome'], cpf=cpf)
        db.session.add(cliente)
        db.session.commit()
        return response(data={'id': cliente.id}, message='Cliente criado.', code=201)
    except Exception as e:
        db.session.rollback()
        return response(error=True, message=str(e), code=409)

@bp.route('/clientes/<int:id>', methods=['GET'])
@auth.login_required
def api_get_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    data = {
        'id': cliente.id,
        'nome': cliente.nome,
        'cpf': cliente.cpf
    }
    return response(data=data)

@bp.route('/clientes/<int:id>', methods=['PUT'])
@auth.login_required
def api_update_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    dados = request.json
    cliente.nome = dados['nome']
    try:
        db.session.commit()
        return response(message='Cliente atualizado.')
    except Exception as e:
        db.session.rollback()
        return response(error=True, message=str(e), code=400)

@bp.route('/clientes/<int:id>', methods=['DELETE'])
@auth.login_required
def api_delete_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    try:
        db.session.delete(cliente)
        db.session.commit()
        return response(message='Cliente excluído.')
    except:
        db.session.rollback()
        return response(error=True, message='Cliente possui vendas.', code=409)

# ------------------- VENDAS -------------------

@bp.route('/vendas', methods=['GET'])
@auth.login_required
def api_listar_vendas():
    vendas = Venda.query.order_by(Venda.criado_em.desc()).all()
    data = [{
        'id': v.id,
        'cliente_id': v.cliente_id,
        'total': str(v.total),
        'criado_em': v.criado_em.isoformat()
    } for v in vendas]
    return response(data=data)

@bp.route('/vendas', methods=['POST'])
@auth.login_required
def api_criar_venda():
    dados = request.json
    cliente_id = dados.get('cliente_id')
    itens = dados.get('itens', [])

    try:
        total = Decimal('0.00')
        with db.session.begin():
            venda = Venda(cliente_id=cliente_id, total=0)
            db.session.add(venda)
            db.session.flush()

            for item in itens:
                produto = Produto.query.get(item['produto_id'])
                qtd = int(item['qtd'])
                preco = produto.preco_unit
                subtotal = preco * qtd
                total += subtotal

                produto.estoque -= qtd
                venda_item = VendaItem(
                    venda_id=venda.id,
                    produto_id=produto.id,
                    quantidade=qtd,
                    preco_unit=preco
                )
                db.session.add(venda_item)

            venda.total = total

        return response(data={'id': venda.id}, message='Venda criada.', code=201)
    except Exception as e:
        db.session.rollback()
        return response(error=True, message=str(e), code=400)

@bp.route('/vendas/<int:id>', methods=['GET'])
@auth.login_required
def api_detalhe_venda(id):
    venda = Venda.query.get_or_404(id)
    data = {
        'id': venda.id,
        'cliente_id': venda.cliente_id,
        'total': str(venda.total),
        'criado_em': venda.criado_em.isoformat(),
        'itens': [{
            'produto_id': item.produto_id,
            'quantidade': item.quantidade,
            'preco_unit': str(item.preco_unit)
        } for item in venda.itens]
    }
    return response(data=data)

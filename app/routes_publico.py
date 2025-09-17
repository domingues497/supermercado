from flask import Blueprint, render_template, redirect, url_for, request, session
from app.models import Produto
from app.routes_cliente import get_cliente

bp = Blueprint('publico', __name__)

@bp.route('/')
def landing():
    produtos = Produto.query.all()
    cliente = get_cliente()

    # Montar carrinho bonitinho
    carrinho_data = session.get("carrinho", {})
    carrinho = []
    for produto_id, qtd in carrinho_data.items():
        produto = Produto.query.get(int(produto_id))
        if produto:
            carrinho.append({
                "produto": produto,
                "quantidade": qtd,
                "subtotal": qtd * produto.preco_unit
            })

    return render_template('landing.html', produtos=produtos, cliente=cliente, carrinho=carrinho)


@bp.route('/carrinho/add/<int:produto_id>', methods=['POST'])
def add_carrinho_publico(produto_id):
    carrinho = session.get('carrinho', {})
    carrinho[str(produto_id)] = carrinho.get(str(produto_id), 0) + 1
    session['carrinho'] = carrinho
    return redirect(url_for('publico.landing'))

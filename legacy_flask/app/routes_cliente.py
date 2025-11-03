from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from app import db
from app.models import Cliente, Produto, Venda, VendaItem
from app.forms import LoginClienteForm, CadastroClienteForm
from app.utils import validar_cpf
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint("cliente", __name__, url_prefix="/cliente")


# Helper para pegar cliente logado
def get_cliente():
    cliente_id = session.get("cliente_id")
    if cliente_id:
        return Cliente.query.get(cliente_id)
    return None


# Helper para carrinho
def get_carrinho():
    return session.get("carrinho", {})


def salvar_carrinho(carrinho):
    session["carrinho"] = carrinho
    session.modified = True


# Login cliente
@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginClienteForm()
    if form.validate_on_submit():
        cpf = "".join(filter(str.isdigit, form.cpf.data))
        cliente = Cliente.query.filter_by(cpf=cpf).first()
        if cliente and check_password_hash(cliente.senha_hash, form.senha.data):
            session["cliente_id"] = cliente.id
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("publico.landing"))
        else:
            flash("CPF ou senha inválidos", "danger")
    return render_template("cliente/login.html", form=form)


# Cadastro cliente
@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    form = CadastroClienteForm()
    if form.validate_on_submit():
        cpf = "".join(filter(str.isdigit, form.cpf.data))
        if not validar_cpf(cpf):
            flash("CPF inválido", "danger")
            return render_template("cliente/cadastro.html", form=form)

        existente = Cliente.query.filter_by(cpf=cpf).first()
        if existente:
            flash("CPF já cadastrado", "danger")
            return render_template("cliente/cadastro.html", form=form)

        cliente = Cliente(nome=form.nome.data, cpf=cpf)
        cliente.senha_hash = generate_password_hash(form.senha.data)

        try:
            db.session.add(cliente)
            db.session.commit()
            session["cliente_id"] = cliente.id
            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("publico.landing"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao cadastrar cliente: " + str(e), "danger")

    return render_template("cliente/cadastro.html", form=form)


# Logout
@bp.route("/logout")
def logout():
    session.pop("cliente_id", None)
    session.pop("carrinho", None)
    flash("Sessão encerrada com sucesso.", "success")
    return redirect(url_for("publico.landing"))


# Adicionar item ao carrinho
@bp.route("/carrinho/add/<int:produto_id>", methods=["POST"])
def add_carrinho(produto_id):
    cliente = get_cliente()
    if not cliente:
        flash("É necessário estar logado para adicionar ao carrinho.", "warning")
        return redirect(url_for("cliente.login"))

    carrinho = get_carrinho()
    carrinho[str(produto_id)] = carrinho.get(str(produto_id), 0) + 1
    salvar_carrinho(carrinho)
    flash("Produto adicionado ao carrinho!", "success")
    return redirect(url_for("publico.landing"))


# Remover item do carrinho
@bp.route("/carrinho/remove/<int:produto_id>", methods=["POST"])
def remove_carrinho(produto_id):
    carrinho = get_carrinho()
    if str(produto_id) in carrinho:
        carrinho.pop(str(produto_id))
        salvar_carrinho(carrinho)
        flash("Produto removido do carrinho.", "info")
    return redirect(url_for("publico.landing"))


# Atualizar quantidade do carrinho
@bp.route("/carrinho/update/<int:produto_id>", methods=["POST"])
def update_carrinho(produto_id):
    quantidade = int(request.form.get("quantidade", 1))
    carrinho = get_carrinho()
    if str(produto_id) in carrinho:
        carrinho[str(produto_id)] = max(1, quantidade)
        salvar_carrinho(carrinho)
        flash("Quantidade atualizada.", "success")
    return redirect(url_for("publico.landing"))


# Finalizar venda
@bp.route("/venda/finalizar", methods=["POST"])
def finalizar_venda():
    cliente = get_cliente()
    if not cliente:
        flash("É necessário estar logado para finalizar a compra.", "warning")
        return redirect(url_for("cliente.login"))

    carrinho = get_carrinho()
    if not carrinho:
        flash("Carrinho vazio.", "warning")
        return redirect(url_for("publico.landing"))

    venda = Venda(cliente_id=cliente.id, total=0)
    db.session.add(venda)

    total = 0
    mensagens = []

    for produto_id, qtd in carrinho.items():
        produto = Produto.query.get(int(produto_id))
        if not produto:
            continue

        preco_unit = produto.preco_unit
        subtotal = preco_unit * qtd

        if produto.estoque >= qtd:
            produto.estoque -= qtd
        else:
            mensagens.append(
                f"Produto {produto.nome} sem estoque suficiente. Será entregue posteriormente."
            )
            if produto.estoque > 0:
                subtotal = preco_unit * produto.estoque
                venda_item = VendaItem(
                    venda=venda,
                    produto=produto,
                    quantidade=produto.estoque,
                    preco_unit=preco_unit,
                )
                db.session.add(venda_item)
                total += subtotal
                produto.estoque = 0
            continue

        venda_item = VendaItem(
            venda=venda, produto=produto, quantidade=qtd, preco_unit=preco_unit
        )
        db.session.add(venda_item)
        total += subtotal

    venda.total = total
    db.session.commit()

    session.pop("carrinho", None)

    flash("Venda finalizada com sucesso!", "success")
    for msg in mensagens:
        flash(msg, "warning")

    return redirect(url_for("publico.landing"))

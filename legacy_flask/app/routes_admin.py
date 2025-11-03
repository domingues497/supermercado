from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Produto, Cliente, Venda, VendaItem, AdminUser
from app.forms import ProdutoForm, ClienteForm, LoginAdminForm
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

bp = Blueprint('admin', __name__)

# ------------------ LOGIN ------------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginAdminForm()
    if form.validate_on_submit():
        admin = AdminUser.query.filter_by(email=form.email.data).first()
        if admin and admin.verificar_senha(form.senha.data):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        flash('Credenciais inválidas.', 'danger')
    return render_template('admin/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

# ------------------ DASHBOARD ------------------

@bp.route('/')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')

# ------------------ PRODUTOS ------------------

@bp.route('/produtos')
@login_required
def listar_produtos():
    termo = request.args.get('search', '')
    produtos = Produto.query.filter(Produto.nome.ilike(f'%{termo}%')).order_by(Produto.nome).all()
    return render_template('admin/produtos/listar.html', produtos=produtos)

@bp.route('/produtos/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    form = ProdutoForm()
    if form.validate_on_submit():
        p = Produto(
            nome=form.nome.data,
            descricao=form.descricao.data,
            preco_unit=form.preco_unit.data,
            estoque=form.estoque.data,
            imagem=form.imagem.data  # salva link da imagem
        )
        db.session.add(p)
        db.session.commit()
        flash('Produto criado com sucesso.', 'success')
        return redirect(url_for('admin.listar_produtos'))
    return render_template('admin/produtos/form.html', form=form)

@bp.route('/produtos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    form = ProdutoForm(obj=produto)
    if form.validate_on_submit():
        produto.nome = form.nome.data
        produto.descricao = form.descricao.data
        produto.preco_unit = form.preco_unit.data
        produto.estoque = form.estoque.data
        produto.imagem = form.imagem.data  # garante que a imagem seja atualizada

        db.session.commit()
        flash('Produto atualizado com sucesso.', 'success')
        return redirect(url_for('admin.listar_produtos'))
    return render_template('admin/produtos/form.html', form=form)

@bp.route('/produtos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    try:
        db.session.delete(produto)
        db.session.commit()
        flash('Produto excluído.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Produto não pode ser excluído: já utilizado em venda.', 'danger')
    return redirect(url_for('admin.listar_produtos'))

# ------------------ CLIENTES ------------------

@bp.route('/clientes')
@login_required
def listar_clientes():
    termo = request.args.get('search', '')
    clientes = Cliente.query.filter(
        (Cliente.nome.ilike(f'%{termo}%')) | (Cliente.cpf.ilike(f'%{termo}%'))
    ).order_by(Cliente.nome).all()
    return render_template('admin/clientes/listar.html', clientes=clientes)

@bp.route('/clientes/novo', methods=['GET', 'POST'])
@login_required
def novo_cliente():
    form = ClienteForm()
    if form.validate_on_submit():
        try:
            cliente = Cliente(nome=form.nome.data, cpf=form.cpf.data)
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente criado com sucesso.', 'success')
            return redirect(url_for('admin.listar_clientes'))
        except IntegrityError:
            db.session.rollback()
            flash('CPF já cadastrado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(str(e), 'danger')
    return render_template('admin/clientes/form.html', form=form)

@bp.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(obj=cliente)
    if request.method == 'POST' and form.validate():
        cliente.nome = form.nome.data
        try:
            db.session.commit()
            flash('Cliente atualizado com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(str(e), 'danger')
        return redirect(url_for('admin.listar_clientes'))
    form.cpf.data = cliente.cpf  # read-only
    return render_template('admin/clientes/form.html', form=form)

@bp.route('/clientes/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso.', 'success')
    except Exception:
        db.session.rollback()
        flash('Cliente não pode ser excluído: possui vendas.', 'danger')
    return redirect(url_for('admin.listar_clientes'))

# ------------------ VENDAS ------------------

@bp.route('/vendas')
@login_required
def listar_vendas():
    vendas = Venda.query.order_by(Venda.criado_em.desc()).all()
    return render_template('admin/vendas/listar.html', vendas=vendas)

@bp.route('/vendas/<int:id>')
@login_required
def detalhe_venda(id):
    venda = Venda.query.get_or_404(id)
    return render_template('admin/vendas/detalhe.html', venda=venda)

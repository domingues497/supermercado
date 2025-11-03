from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .models import Produto
from django.shortcuts import redirect
from django.urls import reverse
from decimal import Decimal
from django.db import transaction
from .models import Venda, VendaItem
from django.contrib import messages


def home(request):
    produtos = Produto.objects.all().order_by('nome')
    return render(request, 'landing.html', { 'produtos': produtos })


def login_view(request):
    return render(request, 'login.html')


def carrinho(request):
    carrinho = request.session.get('carrinho', {})
    itens = []
    total = Decimal('0.00')
    for pid_str, qtd in carrinho.items():
        try:
            produto = Produto.objects.get(id=int(pid_str))
        except Produto.DoesNotExist:
            continue
        subtotal = Decimal(str(produto.preco_unit)) * qtd
        total += subtotal
        itens.append({
            'produto': produto,
            'quantidade': qtd,
            'subtotal': subtotal,
        })
    return render(request, 'carrinho.html', { 'itens': itens, 'total': total })


def carrinho_adicionar(request, produto_id):
    if request.method != 'POST':
        return redirect(reverse('home'))
    try:
        produto = Produto.objects.get(id=produto_id)
    except Produto.DoesNotExist:
        messages.error(request, 'Produto não encontrado.')
        return redirect(reverse('home'))

    carrinho = request.session.get('carrinho', {})
    key = str(produto_id)
    atual = int(carrinho.get(key, 0))

    if produto.estoque is not None and atual >= produto.estoque:
        messages.error(request, f'Estoque insuficiente para adicionar mais "{produto.nome}".')
    else:
        carrinho[key] = atual + 1
        request.session['carrinho'] = carrinho
        messages.success(request, f'"{produto.nome}" adicionado ao carrinho.')
    return redirect(reverse('home'))


def carrinho_remover(request, produto_id):
    if request.method != 'POST':
        return redirect(reverse('carrinho'))
    carrinho = request.session.get('carrinho', {})
    key = str(produto_id)
    if key in carrinho:
        carrinho.pop(key)
        request.session['carrinho'] = carrinho
        messages.info(request, 'Item removido do carrinho.')
    return redirect(reverse('carrinho'))


def carrinho_limpar(request):
    if request.method != 'POST':
        return redirect(reverse('carrinho'))
    request.session['carrinho'] = {}
    messages.info(request, 'Carrinho limpo.')
    return redirect(reverse('carrinho'))

def carrinho_atualizar(request, produto_id):
    if request.method != 'POST':
        return redirect(reverse('carrinho'))
    try:
        produto = Produto.objects.get(id=produto_id)
    except Produto.DoesNotExist:
        messages.error(request, 'Produto não encontrado.')
        return redirect(reverse('carrinho'))

    qtd_raw = request.POST.get('quantidade', '')
    try:
        qtd = int(qtd_raw)
    except (TypeError, ValueError):
        messages.error(request, 'Quantidade inválida.')
        return redirect(reverse('carrinho'))

    if qtd <= 0:
        # Remover se quantidade zero ou negativa
        carrinho = request.session.get('carrinho', {})
        carrinho.pop(str(produto_id), None)
        request.session['carrinho'] = carrinho
        messages.info(request, f'"{produto.nome}" removido do carrinho.')
        return redirect(reverse('carrinho'))

    # Limitar ao estoque disponível
    if produto.estoque is not None and qtd > produto.estoque:
        qtd = produto.estoque
        messages.warning(request, f'Quantidade ajustada ao estoque disponível ({qtd}).')

    carrinho = request.session.get('carrinho', {})
    carrinho[str(produto_id)] = qtd
    request.session['carrinho'] = carrinho
    messages.success(request, f'Quantidade de "{produto.nome}" atualizada para {qtd}.')
    return redirect(reverse('carrinho'))


@transaction.atomic
def carrinho_finalizar(request):
    if request.method != 'POST':
        return redirect(reverse('carrinho'))
    carrinho = request.session.get('carrinho', {})
    if not carrinho:
        return redirect(reverse('carrinho'))

    total = Decimal('0.00')
    itens_validos = []
    for pid_str, qtd in carrinho.items():
        try:
            produto = Produto.objects.get(id=int(pid_str))
        except Produto.DoesNotExist:
            continue
        qtd_int = int(qtd)
        if qtd_int <= 0:
            continue
        preco = Decimal(str(produto.preco_unit))
        subtotal = preco * qtd_int
        # Valida estoque antes de prosseguir
        if produto.estoque is not None and produto.estoque < qtd_int:
            messages.error(request, f'Estoque insuficiente para "{produto.nome}". Disponível: {produto.estoque}, solicitado: {qtd_int}.')
            return redirect(reverse('carrinho'))
        total += subtotal
        itens_validos.append((produto, qtd_int, preco))

    venda = Venda.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        total=total
    )
    for produto, qtd_int, preco in itens_validos:
        VendaItem.objects.create(
            venda=venda,
            produto=produto,
            quantidade=qtd_int,
            preco_unit=preco
        )
        # Decrementa estoque
        produto.estoque = max(0, (produto.estoque or 0) - qtd_int)
        produto.save(update_fields=['estoque'])

    # Limpa carrinho após finalizar
    request.session['carrinho'] = {}
    messages.success(request, 'Compra finalizada com sucesso!')
    return redirect(reverse('home'))


@login_required
def dashboard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Acesso negado: é necessário ser administrador.")
    # Dados de exemplo; posteriormente podemos alimentar com métricas reais
    context = {
        'stats': {
            'usuarios': 0,
            'pedidos': 0,
            'receita': 0,
        }
    }
    return render(request, 'dashboard.html', context)

# Create your views here.

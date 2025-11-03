from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
from .models import Produto, Venda, VendaItem, Cliente
from .forms import CadastroClienteForm, LoginForm


def home(request):
    produtos = Produto.objects.all().order_by('nome')
    return render(request, 'landing.html', { 'produtos': produtos })


def cadastro_view(request):
    if request.method == 'POST':
        form = CadastroClienteForm(request.POST)
        if form.is_valid():
            # Cria o usuário
            user = form.save()
            user.first_name = form.cleaned_data['first_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Cria o cliente
            Cliente.objects.create(
                usuario=user,
                cpf=form.cleaned_data['cpf'],
                data_nascimento=form.cleaned_data['data_nascimento'],
                cep=form.cleaned_data['cep'],
                logradouro=form.cleaned_data['logradouro'],
                numero=form.cleaned_data['numero'],
                complemento=form.cleaned_data['complemento'],
                bairro=form.cleaned_data['bairro'],
                cidade=form.cleaned_data['cidade'],
                estado=form.cleaned_data['estado'],
                pais=form.cleaned_data['pais'],
                ponto_referencia=form.cleaned_data['ponto_referencia'],
                telefone_celular=form.cleaned_data['telefone_celular'],
                telefone_fixo=form.cleaned_data['telefone_fixo'],
                preferencia_contato=form.cleaned_data['preferencia_contato'],
            )
            
            messages.success(request, 'Cadastro realizado com sucesso! Faça login para continuar.')
            return redirect('login')
    else:
        form = CadastroClienteForm()
    
    return render(request, 'cadastro.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Tenta autenticar por username
            user = authenticate(request, username=username_or_email, password=password)
            
            # Se não conseguiu, tenta por email
            if user is None:
                try:
                    from django.contrib.auth.models import User
                    user_by_email = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_by_email.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
                
                # Redireciona para onde estava tentando ir ou para home
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Você foi desconectado.')
    return redirect('home')


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


@login_required
def finalizar_compra(request):
    carrinho = request.session.get('carrinho', {})
    
    if not carrinho:
        messages.error(request, 'Seu carrinho está vazio.')
        return redirect('carrinho')
    
    # Verificar se o usuário tem um perfil de cliente
    try:
        cliente = Cliente.objects.get(usuario=request.user)
    except Cliente.DoesNotExist:
        messages.error(request, 'Você precisa completar seu cadastro para finalizar a compra.')
        return redirect('cadastro')
    
    try:
        with transaction.atomic():
            # Criar a venda
            venda = Venda.objects.create(usuario=request.user)
            
            total = Decimal('0.00')
            
            # Criar os itens da venda
            for produto_id, quantidade in carrinho.items():
                produto = Produto.objects.get(id=produto_id)
                
                # Verificar se há estoque suficiente
                if produto.estoque < quantidade:
                    messages.error(request, f'Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque}')
                    return redirect('carrinho')
                
                # Criar item da venda
                VendaItem.objects.create(
                    venda=venda,
                    produto=produto,
                    quantidade=quantidade,
                    preco_unitario=produto.preco
                )
                
                # Atualizar estoque
                produto.estoque -= quantidade
                produto.save()
                
                total += produto.preco * quantidade
            
            # Atualizar total da venda
            venda.total = total
            venda.save()
            
            # Limpar carrinho
            request.session['carrinho'] = {}
            
            messages.success(request, f'Compra finalizada com sucesso! Total: R$ {total:.2f}')
            return redirect('home')
            
    except Exception as e:
        messages.error(request, 'Erro ao processar a compra. Tente novamente.')
        return redirect('carrinho')


@login_required
@transaction.atomic
def carrinho_finalizar(request):
    if request.method != 'POST':
        return redirect(reverse('carrinho'))
    carrinho = request.session.get('carrinho', {})
    if not carrinho:
        return redirect(reverse('carrinho'))

    # Confere se o cliente possui cadastro completo antes de finalizar
    cliente = Cliente.objects.filter(usuario=request.user).first()
    if not cliente:
        messages.error(request, 'Para finalizar a compra, você precisa completar seu cadastro.')
        return redirect(reverse('cadastro'))

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

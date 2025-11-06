from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
import uuid
import json
import re
from urllib.request import urlopen
from urllib.error import URLError
from .models import Produto, Venda, VendaItem, Cliente
from .forms import CadastroClienteForm, LoginForm, UserUpdateForm, ClienteUpdateForm


def home(request):
    produtos = Produto.objects.all().order_by('nome')
    return render(request, 'landing.html', { 'produtos': produtos })


@login_required
def meus_pedidos(request):
    # Lista as vendas do usuário autenticado com seus itens
    vendas = (
        Venda.objects.filter(usuario=request.user)
        .order_by('-criado_em')
        .prefetch_related('itens', 'itens__produto')
    )
    return render(request, 'pedidos.html', { 'vendas': vendas })


# --- CEP Lookup helpers ---
def _fetch_cep_viacep(cep):
    try:
        with urlopen(f'https://viacep.com.br/ws/{cep}/json/', timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('erro'):
                return None
            return {
                'logradouro': data.get('logradouro', ''),
                'bairro': data.get('bairro', ''),
                'cidade': data.get('localidade', ''),
                'estado': data.get('uf', ''),
            }
    except URLError:
        return None
    except Exception:
        return None


def _fetch_cep_brasilapi(cep):
    try:
        with urlopen(f'https://brasilapi.com.br/api/cep/v2/{cep}', timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if 'message' in data:
                return None
            return {
                'logradouro': data.get('street', ''),
                'bairro': data.get('neighborhood', ''),
                'cidade': data.get('city', ''),
                'estado': data.get('state', ''),
            }
    except URLError:
        return None
    except Exception:
        return None


def buscar_cep(cep):
    """Busca CEP com fallback entre ViaCEP e BrasilAPI."""
    cep_digits = re.sub(r'\D', '', cep)
    if len(cep_digits) != 8:
        return None
    return _fetch_cep_viacep(cep_digits) or _fetch_cep_brasilapi(cep_digits)


def cep_lookup(request, cep):
    """Endpoint JSON para buscar endereço por CEP."""
    result = buscar_cep(cep)
    if not result:
        return JsonResponse({'error': 'CEP inválido ou não encontrado'}, status=404)
    return JsonResponse({'cep': re.sub(r'\D', '', cep), **result})


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
                forma_pagamento_preferida=form.cleaned_data['forma_pagamento_preferida'],
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
                
                # Redireciona para 'next' se presente
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)

                # Se for admin/staff ou e-mail específico, leva para o Django Admin
                try:
                    user_email = (user.email or '').lower()
                except Exception:
                    user_email = ''
                if user.is_superuser or user.is_staff or user_email == 'admin@supermercado.local':
                    return redirect(reverse('admin:index'))

                # Caso padrão: home
                return redirect('home')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Você foi desconectado.')
    # Respeita parâmetro "next" para redirecionar após logout
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect('home')


@login_required
def perfil(request):
    cliente = Cliente.objects.filter(usuario=request.user).first()
    if not cliente:
        messages.info(request, 'Complete seu cadastro para editar seus dados.')
        return redirect('cadastro')

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        cliente_form = ClienteUpdateForm(request.POST, instance=cliente)
        if user_form.is_valid() and cliente_form.is_valid():
            with transaction.atomic():
                user_form.save()
                cliente_form.save()
            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('perfil')
    else:
        user_form = UserUpdateForm(instance=request.user)
        cliente_form = ClienteUpdateForm(instance=cliente)

    return render(request, 'perfil.html', {
        'user_form': user_form,
        'cliente_form': cliente_form,
    })


@login_required
def conta_excluir(request):
    if request.method == 'POST':
        # Deleta o usuário; o Cliente relacionado é removido por cascata
        u = request.user
        logout(request)
        try:
            u.delete()
            messages.info(request, 'Sua conta foi excluída com sucesso.')
        except Exception:
            messages.error(request, 'Não foi possível excluir sua conta. Tente novamente.')
        return redirect('home')

    return render(request, 'conta_excluir.html')


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
    # Opções de pagamento e preferência do usuário
    pagamento_opcoes = [
        ('pix', 'Pix'),
        ('credito', 'Cartão de crédito'),
        ('debito', 'Cartão de débito'),
        ('boleto', 'Boleto'),
    ]
    preferida = None
    if request.user.is_authenticated:
        cliente = Cliente.objects.filter(usuario=request.user).first()
        if cliente:
            preferida = getattr(cliente, 'forma_pagamento_preferida', None)
    return render(request, 'carrinho.html', { 'itens': itens, 'total': total, 'pagamento_opcoes': pagamento_opcoes, 'preferida': preferida })


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
    itens_validos = []  # (produto, qtd_int, preco, backorder)
    itens_em_falta = []
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
        # Se estoque for insuficiente, permite compra e marca para entrega posterior
        backorder = produto.estoque < qtd_int
        if backorder:
            itens_em_falta.append(produto)
        total += subtotal
        itens_validos.append((produto, qtd_int, preco, backorder))

    # Determina forma de pagamento escolhida
    forma = (request.POST.get('forma_pagamento') or '').strip()
    formas_validas = {'pix', 'credito', 'debito', 'boleto'}
    if not forma or forma not in formas_validas:
        forma = cliente.forma_pagamento_preferida if cliente and cliente.forma_pagamento_preferida in formas_validas else 'pix'

    venda = Venda.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        total=total,
        forma_pagamento=forma,
        confirmacao_token=str(uuid.uuid4()),
        status='novo'
    )
    for produto, qtd_int, preco, backorder in itens_validos:
        VendaItem.objects.create(
            venda=venda,
            produto=produto,
            quantidade=qtd_int,
            preco_unit=preco,
            backorder=backorder
        )
        # Decrementa estoque (não permitindo negativo)
        produto.estoque = max(0, (produto.estoque or 0) - qtd_int)
        produto.save(update_fields=['estoque'])

    # Limpa carrinho após finalizar
    request.session['carrinho'] = {}
    messages.success(request, 'Compra finalizada com sucesso!')
    if itens_em_falta:
        nomes = ', '.join(p.nome for p in itens_em_falta)
        messages.warning(request, f'Os produtos {nomes} estão em falta e serão entregues posteriormente.')
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

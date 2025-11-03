from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Cliente
import re
from datetime import date


def validar_cpf(cpf):
    """Valida CPF brasileiro"""
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    # Verifica se os dígitos calculados conferem
    return cpf[9] == str(digito1) and cpf[10] == str(digito2)


class CadastroClienteForm(UserCreationForm):
    # Dados pessoais obrigatórios
    first_name = forms.CharField(
        max_length=150, 
        label="Nome completo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu nome completo'})
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'})
    )
    cpf = forms.CharField(
        max_length=14,
        label="CPF",
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '000.000.000-00',
            'data-mask': '000.000.000-00'
        })
    )
    data_nascimento = forms.DateField(
        label="Data de nascimento",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Endereço completo
    cep = forms.CharField(
        max_length=9,
        label="CEP",
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '00000-000',
            'data-mask': '00000-000'
        })
    )
    logradouro = forms.CharField(
        max_length=200,
        label="Rua/Logradouro",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da rua'})
    )
    numero = forms.CharField(
        max_length=10,
        label="Número",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123'})
    )
    complemento = forms.CharField(
        max_length=100,
        label="Complemento",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apto, bloco, etc. (opcional)'})
    )
    bairro = forms.CharField(
        max_length=100,
        label="Bairro",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do bairro'})
    )
    cidade = forms.CharField(
        max_length=100,
        label="Cidade",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da cidade'})
    )
    estado = forms.CharField(
        max_length=2,
        label="Estado",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SP', 'maxlength': '2'})
    )
    pais = forms.CharField(
        max_length=50,
        label="País",
        initial="Brasil",
        widget=forms.TextInput(attrs={'class': 'form-control', 'value': 'Brasil'})
    )
    ponto_referencia = forms.CharField(
        max_length=200,
        label="Ponto de referência",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Próximo ao... (opcional)'})
    )
    
    # Contatos
    telefone_celular = forms.CharField(
        max_length=15,
        label="Telefone celular (WhatsApp)",
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '(11) 99999-9999',
            'data-mask': '(00) 00000-0000'
        })
    )
    telefone_fixo = forms.CharField(
        max_length=14,
        label="Telefone fixo",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '(11) 3333-3333 (opcional)',
            'data-mask': '(00) 0000-0000'
        })
    )
    preferencia_contato = forms.ChoiceField(
        choices=[
            ('email', 'E-mail'),
            ('whatsapp', 'WhatsApp'),
            ('sms', 'SMS'),
        ],
        label="Preferência de contato",
        initial='whatsapp',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nome de usuário'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Senha'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirme a senha'})
        
        # Customiza labels
        self.fields['username'].label = "Nome de usuário"
        self.fields['password1'].label = "Senha"
        self.fields['password2'].label = "Confirme a senha"

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf and not validar_cpf(cpf):
            raise forms.ValidationError("CPF inválido.")
        
        # Remove formatação para salvar
        cpf_limpo = re.sub(r'[^0-9]', '', cpf)
        
        # Verifica se já existe
        if Cliente.objects.filter(cpf=cpf_limpo).exists():
            raise forms.ValidationError("Este CPF já está cadastrado.")
            
        return cpf_limpo

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

    def clean_data_nascimento(self):
        data_nasc = self.cleaned_data.get('data_nascimento')
        if data_nasc:
            hoje = date.today()
            idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
            if idade < 16:
                raise forms.ValidationError("Você deve ter pelo menos 16 anos para se cadastrar.")
            if idade > 120:
                raise forms.ValidationError("Data de nascimento inválida.")
        return data_nasc

    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        if cep:
            # Remove formatação
            cep_limpo = re.sub(r'[^0-9]', '', cep)
            if len(cep_limpo) != 8:
                raise forms.ValidationError("CEP deve ter 8 dígitos.")
            return cep_limpo
        return cep

    def clean_estado(self):
        estado = self.cleaned_data.get('estado')
        if estado:
            return estado.upper()
        return estado


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Nome de usuário ou e-mail",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu usuário ou e-mail'})
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua senha'})
    )
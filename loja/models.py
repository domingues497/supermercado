from django.db import models


class Cliente(models.Model):
    # Relacionamento com User do Django
    usuario = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    
    # Dados pessoais obrigatórios
    cpf = models.CharField(max_length=11, unique=True)
    data_nascimento = models.DateField()
    
    # Endereço completo
    cep = models.CharField(max_length=8)
    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    pais = models.CharField(max_length=50, default="Brasil")
    ponto_referencia = models.CharField(max_length=200, blank=True)
    
    # Contatos
    telefone_celular = models.CharField(max_length=15)
    telefone_fixo = models.CharField(max_length=14, blank=True)
    preferencia_contato = models.CharField(
        max_length=10,
        choices=[
            ('email', 'E-mail'),
            ('whatsapp', 'WhatsApp'),
            ('sms', 'SMS'),
        ],
        default='whatsapp'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(cpf__regex=r'^\d{11}$'), name='check_cpf_format'),
        ]

    def __str__(self):
        return f"{self.usuario.first_name} ({self.cpf})"
    
    @property
    def cpf_formatado(self):
        """Retorna CPF formatado: 000.000.000-00"""
        if len(self.cpf) == 11:
            return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        return self.cpf
    
    @property
    def cep_formatado(self):
        """Retorna CEP formatado: 00000-000"""
        if len(self.cep) == 8:
            return f"{self.cep[:5]}-{self.cep[5:]}"
        return self.cep
    
    @property
    def endereco_completo(self):
        """Retorna endereço formatado"""
        endereco = f"{self.logradouro}, {self.numero}"
        if self.complemento:
            endereco += f", {self.complemento}"
        endereco += f" - {self.bairro}, {self.cidade}/{self.estado}"
        endereco += f" - CEP: {self.cep_formatado}"
        return endereco


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco_unit = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.IntegerField(default=0)
    imagem = models.CharField(max_length=200, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(estoque__gte=0), name='check_estoque_non_negative'),
        ]

    def __str__(self):
        return self.nome


class Venda(models.Model):
    usuario = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    criado_em = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Venda #{self.id} - R$ {self.total}"


class VendaItem(models.Model):
    venda = models.ForeignKey(Venda, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.IntegerField()
    preco_unit = models.DecimalField(max_digits=10, decimal_places=2)
    backorder = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(quantidade__gt=0), name='check_quantidade_positive'),
        ]

    def subtotal(self):
        return self.quantidade * self.preco_unit

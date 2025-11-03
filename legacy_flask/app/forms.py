from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Email, ValidationError
from app.utils import validar_cpf

class ProdutoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    preco_unit = DecimalField('Preço Unitário', places=2, rounding=None, validators=[DataRequired()])
    estoque = IntegerField('Estoque', validators=[DataRequired(), NumberRange(min=0)])
    imagem = StringField("Link da Imagem", validators=[Length(max=255)]) 
    submit = SubmitField('Salvar')

class ClienteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])

    def validate_cpf(self, field):
        cpf = ''.join(filter(str.isdigit, field.data))
        if not validar_cpf(cpf):
            raise ValidationError('CPF inválido.')

class LoginAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class LoginClienteForm(FlaskForm):
    cpf = StringField("CPF", validators=[DataRequired(), Length(min=11, max=11)])
    senha = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")

class CadastroClienteForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
    cpf = StringField("CPF", validators=[DataRequired(), Length(min=11, max=11)])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Cadastrar")

    def validate_cpf(self, field):
        cpf = ''.join(filter(str.isdigit, field.data))
        if not validar_cpf(cpf):
            raise ValidationError('CPF inválido.')

class EditarNomeClienteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    submit = SubmitField('Salvar')

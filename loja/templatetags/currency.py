from django import template

register = template.Library()

@register.filter(name='currency_br')
def currency_br(value):
    try:
        # Garante duas casas decimais
        num = float(value)
    except (TypeError, ValueError):
        return value
    # Formata com duas casas e prefixo R$
    return f"R$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
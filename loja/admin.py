from django.contrib import admin
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import Produto, Venda, VendaItem

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "preco_unit", "estoque", "imagem_preview", "criado_em", "atualizado_em")
    search_fields = ("nome", "descricao")
    list_filter = ("estoque", "criado_em", "atualizado_em")
    readonly_fields = ("criado_em", "atualizado_em")
    ordering = ("nome",)
    list_per_page = 25
    actions = ["zerar_estoque"]

    def imagem_preview(self, obj):
        if obj.imagem:
            return mark_safe(f'<img src="{obj.imagem}" style="height:40px;width:auto;border-radius:4px;" />')
        return "—"
    imagem_preview.short_description = "Imagem"

    def zerar_estoque(self, request, queryset):
        queryset.update(estoque=0)
    zerar_estoque.short_description = "Zerar estoque selecionado"


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "total", "criado_em")
    date_hierarchy = "criado_em"
    readonly_fields = ("criado_em", "total")

    class VendaItemInline(admin.TabularInline):
        model = VendaItem
        extra = 0
        fields = ("produto", "quantidade", "preco_unit")
        autocomplete_fields = ["produto"]

    inlines = [VendaItemInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        venda = form.instance
        # Recalcula total baseado nos itens atuais
        total = Decimal('0.00')
        for item in venda.itens.all():
            total += (item.preco_unit or Decimal('0.00')) * (item.quantidade or 0)
        venda.total = total
        venda.save(update_fields=['total'])
        return instances


@admin.register(VendaItem)
class VendaItemAdmin(admin.ModelAdmin):
    list_display = ("id", "venda", "produto", "quantidade", "preco_unit")

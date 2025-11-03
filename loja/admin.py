from django.contrib import admin
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import Produto, Venda, VendaItem, Cliente

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
    list_display = ("id", "usuario", "total", "criado_em", "qtd_itens")
    date_hierarchy = "criado_em"
    readonly_fields = ("criado_em", "total")
    list_filter = ("usuario", "criado_em")
    search_fields = ("id", "usuario__username")
    ordering = ("-criado_em",)
    list_per_page = 25
    actions = ["exportar_csv"]

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

    def qtd_itens(self, obj):
        return obj.itens.count()
    qtd_itens.short_description = "Itens"

    def exportar_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="vendas.csv"'
        writer = csv.writer(response)
        writer.writerow(["id", "usuario", "total", "criado_em", "qtd_itens"]) 
        for venda in queryset.order_by('id'):
            writer.writerow([
                venda.id,
                venda.usuario.username if venda.usuario else "",
                str(venda.total),
                venda.criado_em.isoformat(),
                venda.itens.count(),
            ])
        return response
    exportar_csv.short_description = "Exportar vendas selecionadas para CSV"


@admin.register(VendaItem)
class VendaItemAdmin(admin.ModelAdmin):
    list_display = ("id", "venda", "produto", "quantidade", "preco_unit")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "email", "telefone", "usuario", "criado_em")
    search_fields = ("nome", "email", "telefone", "documento")
    list_filter = ("criado_em", "atualizado_em")
    readonly_fields = ("criado_em", "atualizado_em")
    ordering = ("nome",)
    list_per_page = 25

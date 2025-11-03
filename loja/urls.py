from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('carrinho/adicionar/<int:produto_id>/', views.carrinho_adicionar, name='carrinho_adicionar'),
    path('carrinho/remover/<int:produto_id>/', views.carrinho_remover, name='carrinho_remover'),
    path('carrinho/atualizar/<int:produto_id>/', views.carrinho_atualizar, name='carrinho_atualizar'),
    path('carrinho/limpar/', views.carrinho_limpar, name='carrinho_limpar'),
    path('carrinho/finalizar/', views.carrinho_finalizar, name='carrinho_finalizar'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
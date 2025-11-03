from django.shortcuts import render


def home(request):
    return render(request, 'landing.html')


def login_view(request):
    return render(request, 'login.html')


def carrinho(request):
    return render(request, 'carrinho.html')

# Create your views here.

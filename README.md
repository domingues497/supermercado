# 🛒 Supermercado Delivery - Flask + PostgreSQL

Sistema completo de delivery para supermercado com:

Área do cliente (login por CPF, carrinho sem JS)  
Painel admin (CRUD de produtos/clientes/vendas)  
API REST segura com autenticação básica  
Regras de integridade (CPF, estoque, vendas)  
UI simples, moderna e sem JavaScript

---

##  Stack

- Python 3.11+
- Flask
- PostgreSQL
- SQLAlchemy + Migrate
- Flask-WTF (formulários)
- Flask-Login (sessões)
- Flask-HTTPAuth (API REST)
- HTML/CSS puro (sem JS)
- `.env` com configurações sensíveis

---

## Instalação

```bash

cd supermercado
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt

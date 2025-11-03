# Supermercado Delivery - Flask + PostgreSQL

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
- HTML/CSS puro
- `.env` com configurações sensíveis

---

## Instalação


Instalar PostgreSql no Windows e popular o Banco
https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
Criar uma pasta chamado Supermercado 
mkdir supermercado
cd supermercado
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt

apos a intalação do PostgreSql, popular o Banco de Dados com o script db.sql
- No pgAdmin, crie um novo banco de dados chamado supermercado
    CREATE USER supermercado WITH PASSWORD 'mercado123';
    ALTER USER supermercado WITH SUPERUSER CREATEDB CREATEROLE REPLICATION;
Criar um schema chamado esupermercado
    CREATE DATABASE supermercado
    WITH OWNER = supermercado
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TEMPLATE = template0;

CREATE SCHEMA esupermercado AUTHORIZATION supermercado;
GRANT ALL PRIVILEGES ON DATABASE supermercado TO supermercado;
GRANT ALL PRIVILEGES ON SCHEMA esupermercado TO supermercado;
ALTER ROLE supermercado SET search_path TO esupermercado, public;


criar superusuário

- Ative o ambiente virtual: .\venv\Scripts\activate
- Entre na pasta do projeto: cd supermercado
- Execute: python manage.py createsuperuser
- Preencha os prompts: username , email e password (
- Usuário: admin
- Email: admin@supermercado.local
- Senha: Admin@2025!

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None


def main():
    # Carrega variáveis de ambiente do .env, se possível
    if load_dotenv:
        load_dotenv(Path(".env"))
    else:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if not line or line.strip().startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL não definido no ambiente.")
        sys.exit(1)

    url = urlparse(database_url)
    target_db = url.path.lstrip("/") or "postgres"
    host = url.hostname or "localhost"
    port = url.port or 5432
    user = url.username or "postgres"
    password = url.password or ""

    # Conecta no banco de manutenção 'postgres' para criar o banco alvo
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port,
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (target_db,))
        exists = cur.fetchone() is not None
        if exists:
            print(f"Banco '{target_db}' já existe.")
        else:
            cur.execute(f"CREATE DATABASE \"{target_db}\" ENCODING 'UTF8'")
            print(f"Banco '{target_db}' criado com sucesso.")
        cur.close()
    except psycopg2.Error as e:
        print("Falha ao criar/verificar banco:", e)
        sys.exit(1)
    finally:
        if conn:
            conn.close()

    # Cria schema dedicado, se definido
    schema = os.getenv("DB_SCHEMA")
    if schema:
        try:
            conn2 = psycopg2.connect(
                dbname=target_db,
                user=user,
                password=password,
                host=host,
                port=port,
            )
            conn2.autocommit = True
            cur2 = conn2.cursor()
            cur2.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name=%s", (schema,))
            exists_schema = cur2.fetchone() is not None
            if exists_schema:
                print(f"Schema '{schema}' já existe.")
            else:
                cur2.execute(f"CREATE SCHEMA \"{schema}\" AUTHORIZATION \"{user}\"")
                print(f"Schema '{schema}' criado com sucesso.")
            cur2.close()
            conn2.close()
        except psycopg2.Error as e:
            print("Falha ao criar/verificar schema:", e)
            sys.exit(1)


if __name__ == "__main__":
    main()
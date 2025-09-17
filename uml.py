import os
from app.models import db, Produto, Cliente, Venda, VendaItem, AdminUser
from sqlalchemy.inspection import inspect

OUTPUT_FILE = "models.puml"

def write_class(f, cls):
    """Gera a classe UML para cada model"""
    table = cls.__tablename__
    mapper = inspect(cls)

    f.write(f"class {cls.__name__} {{\n")
    for column in mapper.columns:
        col_type = str(column.type)
        f.write(f"  {column.name} : {col_type}\n")
    f.write("}\n\n")

def write_relationships(f, classes):
    """Cria relacionamentos 1:N e N:N"""
    for cls in classes:
        mapper = inspect(cls)
        for rel in mapper.relationships:
            target = rel.mapper.class_.__name__
            if rel.uselist:  # lista -> N
                f.write(f"{cls.__name__} \"1\" -- \"N\" {target}\n")
            else:  # single -> 1
                f.write(f"{cls.__name__} \"1\" -- \"1\" {target}\n")

def generate_puml():
    models = [Produto, Cliente, Venda, VendaItem, AdminUser]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("@startuml\n\n")

        # Classes
        for model in models:
            write_class(f, model)

        # Relacionamentos
        write_relationships(f, models)

        f.write("\n@enduml\n")

    print(f"✅ Diagrama gerado em {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_puml()

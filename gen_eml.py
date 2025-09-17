import inspect
import os
import pkgutil
import importlib
from app import models
from app.models import db

OUTPUT_FILE = "diagram.puml"

def is_model_class(obj):
    """Checa se uma classe é um modelo do SQLAlchemy."""
    return inspect.isclass(obj) and issubclass(obj, db.Model) and obj is not db.Model

def get_models(module):
    """Retorna todas as classes que são modelos dentro de um módulo."""
    return [cls for name, cls in inspect.getmembers(module, is_model_class)]

def generate_puml(models):
    lines = ["@startuml", "skinparam classAttributeIconSize 0\n"]

    for model in models:
        lines.append(f"class {model.__name__} {{")

        # Atributos
        for col in model.__table__.columns:
            col_type = str(col.type)
            visibility = "-"
            lines.append(f"  {visibility} {col.name} : {col_type}")

        lines.append("}\n")

    # Relacionamentos (1:N, FK)
    for model in models:
        for col in model.__table__.columns:
            if col.foreign_keys:
                for fk in col.foreign_keys:
                    target = fk.column.table.name.capitalize()
                    lines.append(f"{model.__name__} --> {target}")

    lines.append("@enduml")
    return "\n".join(lines)

def main():
    # Coleta modelos do arquivo app/models.py
    model_classes = get_models(models)

    puml_code = generate_puml(model_classes)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(puml_code)

    print(f"✅ Diagrama gerado em {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

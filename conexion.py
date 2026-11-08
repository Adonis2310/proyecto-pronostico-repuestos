import pandas as pd
from sqlalchemy import create_engine, text

servidor = r"PC_ADONIS\SQLEXPRESS"
base = "repuestos"

cadena = (
    f"mssql+pyodbc://@{servidor}/{base}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)

engine = create_engine(cadena)

with engine.connect() as conn:
    total = conn.execute(text("SELECT COUNT(*) FROM ventas_limpias")).scalar()
    print(f"Registros en ventas_limpias: {total}")
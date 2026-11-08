import warnings
import pandas as pd
from sqlalchemy import create_engine
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

# ---------- 1. Conexión ----------
servidor = r"PC_ADONIS\SQLEXPRESS"
base = "repuestos"

cadena = (
    f"mssql+pyodbc://@{servidor}/{base}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)
engine = create_engine(cadena)

# ---------- 2. Serie mensual por producto ----------
query = """
SELECT id_producto,
       DATEFROMPARTS(YEAR(fecha), MONTH(fecha), 1) AS mes,
       SUM(cantidad) AS unidades
FROM ventas_limpias
GROUP BY id_producto, DATEFROMPARTS(YEAR(fecha), MONTH(fecha), 1)
"""
df = pd.read_sql(query, engine)
df["mes"] = pd.to_datetime(df["mes"])

serie = (
    df.set_index(["id_producto", "mes"])["unidades"]
    .unstack(fill_value=0)
    .stack()
    .rename("unidades")
    .reset_index()
)
serie = serie.sort_values(["id_producto", "mes"])

# ---------- 3. Modelo base: promedio de los últimos 3 meses de 2024, repetido en 2025 ----------
resultados_base = []

for producto, grupo in serie.groupby("id_producto"):
    grupo = grupo.sort_values("mes").set_index("mes")["unidades"]
    train = grupo[grupo.index.year < 2025]
    test = grupo[grupo.index.year == 2025]

    nivel = train.iloc[-3:].mean()
    pred = pd.Series(nivel, index=test.index)

    error_abs = (test - pred).abs()
    error_pct = error_abs / test.replace(0, pd.NA) * 100

    resultados_base.append({
        "id_producto": producto,
        "MAE": error_abs.mean(),
        "MAPE_pct": error_pct.mean(),
        "promedio_real": test.mean(),
    })

base_resumen = pd.DataFrame(resultados_base).set_index("id_producto").round(2)
base_resumen.to_csv("datos/resultados_baseline.csv")

# ---------- 4. Holt-Winters: entrenar 2023-2024, probar 2025 ----------
resultados_hw = []

for producto, grupo in serie.groupby("id_producto"):
    grupo = grupo.sort_values("mes").set_index("mes")["unidades"].asfreq("MS")
    train = grupo[grupo.index.year < 2025]
    test = grupo[grupo.index.year == 2025]

    modelo = ExponentialSmoothing(
        train,
        trend="add",
        seasonal="mul",
        seasonal_periods=12,
        damped_trend=True,
    ).fit()

    pred = modelo.forecast(len(test)).clip(lower=0)

    error_abs = (test - pred).abs()
    error_pct = error_abs / test.replace(0, pd.NA) * 100

    resultados_hw.append({
        "id_producto": producto,
        "MAE_hw": error_abs.mean(),
        "MAPE_hw": error_pct.mean(),
    })

hw = pd.DataFrame(resultados_hw).set_index("id_producto").round(2)

# ---------- 5. Comparación ----------
comparacion = base_resumen[["MAE", "MAPE_pct"]].join(hw)
comparacion.to_csv("datos/resultados_comparacion.csv")

print(comparacion.head(10))
print(f"\nMAPE promedio promedio móvil: {comparacion['MAPE_pct'].mean():.2f}%")
print(f"MAPE promedio Holt-Winters:   {comparacion['MAPE_hw'].mean():.2f}%")
print(f"Productos donde Holt-Winters gana: {(comparacion['MAPE_hw'] < comparacion['MAPE_pct']).sum()} de 30")
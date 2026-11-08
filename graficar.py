import warnings
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

# ---------- Conexión y serie mensual ----------
servidor = r"PC_ADONIS\SQLEXPRESS"
base = "repuestos"

cadena = (
    f"mssql+pyodbc://@{servidor}/{base}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)
engine = create_engine(cadena)

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

# ---------- Pronóstico Holt-Winters para un producto ----------
producto_ejemplo = "P003"  # producto de baja rotación, caso difícil

grupo = (
    serie[serie["id_producto"] == producto_ejemplo]
    .sort_values("mes")
    .set_index("mes")["unidades"]
    .asfreq("MS")
)
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

# ---------- Gráfico ----------
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(train.index, train.values, color="gray", label="Histórico (2023-2024)")
ax.plot(test.index, test.values, marker="o", color="#1f77b4", label="Real 2025")
ax.plot(pred.index, pred.values, marker="o", linestyle="--", color="#d62728", label="Pronóstico Holt-Winters")
ax.set_title(f"Ventas mensuales {producto_ejemplo}: real vs. pronóstico 2025")
ax.set_xlabel("Mes")
ax.set_ylabel("Unidades vendidas")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()

fig.savefig(f"datos/grafico_{producto_ejemplo}.png", dpi=150)
print(f"Gráfico guardado en datos/grafico_{producto_ejemplo}.png")
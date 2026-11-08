import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

# Carpeta de salida
salida = Path("datos")
salida.mkdir(exist_ok=True)

# 1. Catálogo de productos
productos = pd.DataFrame({
    "id_producto": [f"P{i:03d}" for i in range(1, 31)],
    "nombre": [
        "Pastilla de freno delantera", "Pastilla de freno trasera", "Disco de freno",
        "Filtro de aceite", "Filtro de aire", "Filtro de gasolina", "Filtro de cabina",
        "Batería 12V 45Ah", "Batería 12V 60Ah", "Batería 12V 75Ah",
        "Aceite 10W-40 1L", "Aceite 5W-30 1L", "Aceite sintético 5W-30 4L", "Grasa multiuso",
        "Bujía estándar", "Bujía de iridio", "Cable de bujía", "Bobina de encendido",
        "Amortiguador delantero", "Amortiguador trasero", "Rótula", "Terminal de dirección",
        "Banda de distribución", "Banda serpentina", "Bomba de agua", "Radiador",
        "Limpiaparabrisas 18\"", "Limpiaparabrisas 22\"", "Líquido refrigerante 1L", "Foco LED H4",
    ],
    "categoria": (
        ["Frenos"] * 3 + ["Filtros"] * 4 + ["Baterías"] * 3 + ["Lubricantes"] * 4 +
        ["Encendido"] * 4 + ["Suspensión"] * 4 + ["Distribución"] * 3 +
        ["Refrigeración"] * 2 + ["Accesorios"] * 2 + ["Iluminación"] * 1
    ),
    "proveedor": np.random.choice(["ProveedorA", "ProveedorB", "ProveedorC"], 30),
    "costo": np.round(np.random.uniform(3, 120, 30), 2),
})

# Ajuste de costos: el precio de venta será costo * 1.4 a 1.8
productos["precio_venta"] = np.round(productos["costo"] * np.random.uniform(1.4, 1.8, 30), 2)

# Demanda base por producto (unidades diarias promedio): unos muy rotativos, otros lentos
demanda_base = np.random.uniform(0.2, 3.0, 30)

# Temporada alta: noviembre y diciembre; baterías y limpiaparabrisas suben antes de lluvias
factor_mes = {1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.1,
              7: 1.0, 8: 1.0, 9: 1.1, 10: 1.2, 11: 1.5, 12: 1.6}

# 2. Ventas diarias 2023-2025
fechas = pd.date_range("2023-01-01", "2025-12-31", freq="D")
registros = []

for idx, prod in productos.iterrows():
    base = demanda_base[idx]
    for f in fechas:
        factor = factor_mes[f.month]
        if prod["categoria"] == "Baterías" and f.month in (4, 5, 9, 10):
            factor *= 1.4  # subida antes de la temporada de lluvias
        tendencia = 1 + 0.05 * (f.year - 2023)  # crecimiento leve del negocio
        lambda_dia = base * factor * tendencia
        cantidad = np.random.poisson(lambda_dia)
        if cantidad > 0:
            registros.append({
                "id_venta": None,
                "fecha": f.date(),
                "id_producto": prod["id_producto"],
                "cantidad": cantidad,
                "precio_unitario": prod["precio_venta"],
            })

ventas = pd.DataFrame(registros)
ventas["id_venta"] = range(1, len(ventas) + 1)
ventas = ventas[["id_venta", "fecha", "id_producto", "cantidad", "precio_unitario"]]

# 3. Errores intencionales para practicar limpieza
n = len(ventas)
# Devoluciones: cantidades negativas (~0.5%)
idx_neg = np.random.choice(n, int(n * 0.005), replace=False)
ventas.loc[idx_neg, "cantidad"] = -ventas.loc[idx_neg, "cantidad"]
# Valores faltantes en precio (~0.3%)
idx_nan = np.random.choice(n, int(n * 0.003), replace=False)
ventas.loc[idx_nan, "precio_unitario"] = np.nan
# IDs de producto que no existen en el catálogo (~0.2%)
idx_bad = np.random.choice(n, int(n * 0.002), replace=False)
ventas.loc[idx_bad, "id_producto"] = "P999"

# Guardar archivos
productos_out = productos[["id_producto", "nombre", "categoria", "proveedor", "costo"]]
productos_out.to_csv(salida / "productos.csv", index=False, encoding="utf-8")
ventas.to_csv(salida / "ventas.csv", index=False, encoding="utf-8")

print(f"Productos: {len(productos_out)} filas")
print(f"Ventas: {len(ventas)} filas")
print("Archivos creados en la carpeta 'datos'.")
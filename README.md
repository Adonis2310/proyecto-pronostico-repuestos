# Pronóstico de demanda para una tienda de repuestos

## Problema de negocio

Una tienda de repuestos pierde ventas en temporada alta porque no reabastece a tiempo los productos de mayor rotación.

**Dueño del problema:** gerente de compras.

**Preguntas que el proyecto responde:**
- ¿Qué productos se agotan más en temporada alta?
- ¿En qué meses alcanza cada producto su pico de ventas?
- ¿Qué método de pronóstico estima mejor la demanda mensual por producto?

## Datos

Los datos son **simulados** con Python (`generar_datos.py`). No provienen de una tienda real.

- **Periodo:** enero 2023 a diciembre 2025 (ventas diarias).
- **Productos:** 30 repuestos en categorías como frenos, filtros, baterías, lubricantes y suspensión.
- **Registros de venta:** 24,181.
- **Patrones introducidos a propósito:** temporada alta en noviembre y diciembre, subida de baterías antes de la temporada de lluvias y un crecimiento anual leve.
- **Errores introducidos a propósito:** devoluciones con cantidad negativa, productos que no existen en el catálogo y precios vacíos.

## Limpieza

Se cargaron los datos en SQL Server (base `repuestos`) y se aplicaron estas reglas:

| Concepto | Registros |
|---|---|
| Registros originales | 24,181 |
| Devoluciones (cantidad negativa) | 120 |
| Productos inexistentes en el catálogo | 48 |
| Precio unitario vacío | 72 |
| **Total descartado** | **240** |
| **Registros limpios para el análisis** | **23,941** |

Los registros descartados se guardaron en la tabla `ventas_descartadas`, para que el proceso sea auditable. El análisis usa la tabla `ventas_limpias`.

## Temporada alta

Se calculó un índice estacional por producto: unidades vendidas en cada mes dividido entre el promedio mensual del producto.

- **29 de 30 productos** alcanzan su pico entre octubre y diciembre.
- **18** tienen su pico en diciembre, **7** en noviembre, **4** en octubre y **1** en junio.

**Nota:** como los datos son simulados, este resultado confirma que el método detecta el patrón introducido. No describe el comportamiento de un negocio real.

## Modelos de pronóstico

Ambos modelos se evaluaron con la misma regla: entrenamiento con 2023 y 2024, y pronóstico de los doce meses de 2025 sin ver esos datos.

- **Modelo base:** promedio de los tres últimos meses de 2024, repetido para todo 2025.
- **Holt-Winters:** suavizamiento exponencial con tendencia amortiguada y estacionalidad multiplicativa de 12 meses.

### Resultados

| Modelo | MAPE promedio |
|---|---|
| Promedio fijo (base) | 34.41% |
| Holt-Winters | 16.86% |

**Holt-Winters gana en 27 de 30 productos.**

Métrica usada: MAPE (error porcentual absoluto medio) y MAE (error absoluto medio en unidades). Los resultados por producto están en `datos/resultados_comparacion.csv`.

## Gráficos

- `datos/grafico_P008.png`: caso en que el modelo sigue bien el patrón de temporada.
- `datos/grafico_P003.png`: caso difícil. Producto de baja rotación donde el modelo no capta la subida final.

## Limitaciones

- Los datos son simulados, así que los resultados demuestran que el método funciona con el patrón definido, no describen un negocio real.
- El pronóstico es a doce meses sin reentrenar el modelo con datos nuevos.
- Para productos de baja rotación (por ejemplo P003 y P010) el error es alto. Para estos productos conviene usar reglas de inventario más simples o revisar con más datos.
- No se consideraron precios, promociones, proveedores ni tiempos de entrega.

## Estructura del repositorio
proyecto-pronostico-repuestos/
├── README.md
├── generar_datos.py # genera los datos simulados
├── conexion.py # prueba la conexión a SQL Server
├── pronostico.py # modelo base y Holt-Winters
├── graficar.py # gráficos real vs. pronóstico
├── datos/ # CSV generados y resultados
├── sql/ # consultas SQL del análisis
└── notebooks/

## Cómo reproducir

1. Ejecutar `python generar_datos.py`.
2. Crear la base `repuestos` en SQL Server e importar `productos.csv` y `ventas.csv`.
3. Ejecutar las consultas de limpieza y temporada alta en `sql/`.
4. Ejecutar `python pronostico.py` y `python graficar.py`.

## Tecnologías

Python (pandas, statsmodels, matplotlib, SQLAlchemy, pyodbc), SQL Server y SQL Server Management Studio.

## Autor
ADONIS FAJARDO ROJAS
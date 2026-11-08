create database repuestos
use repuestos

-- =============================================
-- 1. Conversión de tipos de datos
-- Las columnas se importaron como varchar; se convierten a sus tipos reales.
-- =============================================
ALTER TABLE ventas ALTER COLUMN id_venta INT NOT NULL;
ALTER TABLE ventas ALTER COLUMN fecha DATE NULL;
ALTER TABLE ventas ALTER COLUMN id_producto VARCHAR(10) NULL;
ALTER TABLE ventas ALTER COLUMN cantidad INT NULL;
ALTER TABLE ventas ALTER COLUMN precio_unitario DECIMAL(10,2) NULL;

-- =============================================
-- 2. Corrección de precios vacíos (72 registros)
-- =============================================
UPDATE ventas
SET precio_unitario = NULL
WHERE LTRIM(RTRIM(precio_unitario)) = '';

-- =============================================
-- 3. Detección de problemas: devoluciones e IDs inexistentes
-- Resultado: 120 devoluciones y 48 productos inexistentes
-- =============================================
SELECT
    (SELECT COUNT(*) FROM ventas WHERE cantidad < 0) AS devoluciones,
    (SELECT COUNT(*)
     FROM ventas v
     WHERE NOT EXISTS (
         SELECT 1 FROM productos p
         WHERE p.id_producto = v.id_producto
     )) AS ids_inexistentes;

-- =============================================
-- 4. Tabla de cuarentena y tabla limpia
-- Resultado: 24,181 originales = 240 descartados + 23,941 limpios
-- =============================================
SELECT *
INTO ventas_descartadas
FROM ventas
WHERE cantidad < 0
   OR NOT EXISTS (
        SELECT 1 FROM productos p
        WHERE p.id_producto = ventas.id_producto
   )
   OR precio_unitario IS NULL;

SELECT *
INTO ventas_limpias
FROM ventas
WHERE id_venta NOT IN (SELECT id_venta FROM ventas_descartadas);

SELECT
    (SELECT COUNT(*) FROM ventas) AS ventas_originales,
    (SELECT COUNT(*) FROM ventas_descartadas) AS descartadas,
    (SELECT COUNT(*) FROM ventas_limpias) AS limpias;

-- =============================================
-- 5. Índice estacional por producto (temporada alta)
-- Resultado: 50 filas con índice >= 1.3
-- =============================================
WITH ventas_mensuales AS (
    SELECT
        id_producto,
        MONTH(fecha) AS mes_num,
        SUM(cantidad) AS unidades
    FROM ventas_limpias
    GROUP BY id_producto, MONTH(fecha)
),
indice_estacional AS (
    SELECT
        id_producto,
        mes_num,
        unidades,
        ROUND(unidades * 1.0 / AVG(unidades) OVER (PARTITION BY id_producto), 2) AS indice
    FROM ventas_mensuales
)
SELECT *
FROM indice_estacional
WHERE indice >= 1.3
ORDER BY id_producto, indice DESC;

-- =============================================
-- 6. Mes de pico por producto
-- Resultado: diciembre 18, noviembre 7, octubre 4, junio 1
-- =============================================
WITH ventas_mensuales AS (
    SELECT id_producto, MONTH(fecha) AS mes_num, SUM(cantidad) AS unidades
    FROM ventas_limpias
    GROUP BY id_producto, MONTH(fecha)
),
indice_estacional AS (
    SELECT id_producto, mes_num,
           unidades * 1.0 / AVG(unidades) OVER (PARTITION BY id_producto) AS indice
    FROM ventas_mensuales
),
pico AS (
    SELECT id_producto, mes_num, indice,
           ROW_NUMBER() OVER (PARTITION BY id_producto ORDER BY indice DESC) AS rn
    FROM indice_estacional
)
SELECT mes_num AS mes_pico, COUNT(*) AS productos
FROM pico
WHERE rn = 1
GROUP BY mes_num
ORDER BY productos DESC;
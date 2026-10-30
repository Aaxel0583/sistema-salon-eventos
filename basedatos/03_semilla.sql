-- =====================================================================
-- PKG-06 Base de datos · Script 03 · Carga inicial de catálogos
--
-- Plan de Proyecto §18 (migración de datos): carga de los 3 salones,
-- platillos y paquetes estándar. Los valores de los salones son
-- PROVISIONALES: el gerente los corrige desde Catálogos > Salones con los
-- datos reales del cliente (SRS §4.6, supuesto 1).
-- El primer gerente NO se crea aquí: se crea con la utilidad C-09
--     python -m administracion.admin crear-gerente ...
-- para que su clave se derive con sal desde Python (RNF-04).
-- =====================================================================

BEGIN;

INSERT INTO salon (nombre, descripcion, capacidad_maxima, costo_renta, disponible) VALUES
    ('Salón Principal', 'Salón techado con pista de baile y escenario', 250, 18000.00, 'S'),
    ('Salón Jardín',    'Espacio al aire libre con toldo',              150, 12000.00, 'S'),
    ('Salón Terraza',   'Terraza para eventos íntimos',                  90,  8000.00, 'S');

INSERT INTO platillo (nombre, categoria) VALUES
    ('Crema de elote',                       'ENTRADA'),
    ('Ensalada de la casa',                  'ENTRADA'),
    ('Sopa de tortilla',                     'ENTRADA'),
    ('Pechuga rellena en salsa de chipotle', 'PLATO_FUERTE'),
    ('Filete de res al vino tinto',          'PLATO_FUERTE'),
    ('Lomo de cerdo en salsa de ciruela',    'PLATO_FUERTE'),
    ('Arroz a la mexicana',                  'GUARNICION'),
    ('Puré de papa',                         'GUARNICION'),
    ('Verduras al vapor',                    'GUARNICION'),
    ('Pastel de tres leches',                'POSTRE'),
    ('Flan napolitano',                      'POSTRE'),
    ('Agua fresca de temporada',             'BEBIDA'),
    ('Refresco ilimitado',                   'BEBIDA');

INSERT INTO paquete (nombre, precio_persona, tipo, id_cliente) VALUES
    ('Paquete Clásico',   280.00, 'ESTANDAR', NULL),
    ('Paquete Ejecutivo', 380.00, 'ESTANDAR', NULL),
    ('Paquete Gala',      520.00, 'ESTANDAR', NULL);

-- Composición de cada paquete, relacionada por nombre para no depender
-- de los valores que asigne SERIAL.
INSERT INTO paquete_platillo (id_paquete, id_platillo)
SELECT p.id_paquete, pl.id_platillo
  FROM (VALUES
        ('Paquete Clásico',   'Sopa de tortilla'),
        ('Paquete Clásico',   'Pechuga rellena en salsa de chipotle'),
        ('Paquete Clásico',   'Arroz a la mexicana'),
        ('Paquete Clásico',   'Agua fresca de temporada'),
        ('Paquete Ejecutivo', 'Crema de elote'),
        ('Paquete Ejecutivo', 'Lomo de cerdo en salsa de ciruela'),
        ('Paquete Ejecutivo', 'Puré de papa'),
        ('Paquete Ejecutivo', 'Pastel de tres leches'),
        ('Paquete Ejecutivo', 'Agua fresca de temporada'),
        ('Paquete Gala',      'Ensalada de la casa'),
        ('Paquete Gala',      'Filete de res al vino tinto'),
        ('Paquete Gala',      'Verduras al vapor'),
        ('Paquete Gala',      'Flan napolitano'),
        ('Paquete Gala',      'Refresco ilimitado')
       ) AS c (paquete, platillo)
  JOIN paquete  p  ON p.nombre  = c.paquete
  JOIN platillo pl ON pl.nombre = c.platillo;

COMMIT;

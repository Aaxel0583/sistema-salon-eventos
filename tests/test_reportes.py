"""
Sprint 3 · Reportes operativos (HU-010, HU-011, HU-012 · CU-09).
Casos del SRS Anexo C:
  CP-16 · semáforo de cartera a 5, 30 y −3 días (RF-37, RN-13)
  CP-17 · reportes de proyectos activos y realizados (RF-35, RF-36)
  CP-18 · descarga en CSV con las columnas de la pantalla (RF-38)
"""
import csv
import io
import itertools
import re
from datetime import timedelta
from decimal import Decimal

import pytest

from app.datos.conexion import BaseDatos
from app.datos.repositorio_eventos import RepositorioEventos
from app.datos.repositorio_reportes import RepositorioReportes

pytestmark = pytest.mark.integracion

# Cada evento de este archivo toma su propio horario de madrugada, para no
# encimarse (BF002) con los de otras pruebas que usan la misma fecha relativa.
_turnos = itertools.count()


def _horario():
    n = next(_turnos)
    inicio = f"{n // 6:02d}:{(n % 6) * 10:02d}"
    fin = f"{n // 6:02d}:{(n % 6) * 10 + 9:02d}"
    return inicio, fin


# ------------------------------- apoyo -------------------------------
@pytest.fixture(autouse=True)
def _aplicacion(app):
    """Todas las pruebas del archivo usan el pool de conexiones de la aplicación."""


def _entrar(http, identificador, clave):
    return http.post("/login", data={"identificador": identificador, "clave": clave})


@pytest.fixture
def gerente(cliente_http, crear_usuario):
    id_gerente, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    return id_gerente


def _hoy():
    with BaseDatos.transaccion() as cur:
        return RepositorioEventos(cur).hoy()


def _evento_a(id_cliente, dias, estado="CONFIRMADO", abono=None, id_salon=1, nombre="Reporte"):
    """Evento a `dias` de hoy (negativo = ya pasó). Devuelve su fila de IB-01."""
    inicio, fin = _horario()
    with BaseDatos.transaccion() as cur:
        repo = RepositorioEventos(cur)
        id_evento = repo.insertar(id_cliente, None, id_salon, 1, nombre, repo.hoy() + timedelta(days=dias),
                                  inicio, fin, 40)
        if estado != "COTIZACION":
            repo.actualizar_estado(id_evento, estado)
        if abono:
            cur.execute("SELECT fn_registrar_pago(%s, %s, 'EFECTIVO')", (id_evento, Decimal(str(abono))))
        return repo.por_id(id_evento)


def _cartera(semaforo=None):
    with BaseDatos.transaccion() as cur:
        return {c.id_evento: c for c in RepositorioReportes(cur).cartera(semaforo)}


def _totales():
    with BaseDatos.transaccion() as cur:
        return RepositorioReportes(cur).totales_cartera()


def _fila(texto, evento):
    """El renglón del evento en la tabla del reporte, o None."""
    partes = texto.split(f'href="/eventos/{evento.id_evento}"')
    return partes[1].split("</tr>")[0] if len(partes) > 1 else None


def _csv(respuesta):
    contenido = respuesta.get_data().decode("utf-8-sig")
    return list(csv.reader(io.StringIO(contenido)))


def _encabezados(texto):
    cabecera = texto.split("<thead>")[1].split("</thead>")[0]
    return [re.sub(r"\s+", " ", t).strip() for t in re.findall(r"<th[^>]*>(.*?)</th>", cabecera, re.S)]


# ------------------------------ CP-16 ------------------------------
def test_cp16_semaforo_a_5_30_y_menos_3_dias(crear_usuario):
    """RN-13: 5 días = próxima a vencer, 30 días = vigente, −3 días = vencida."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    proximo, vigente, vencido = (_evento_a(id_cliente, d) for d in (5, 30, -3))
    cartera = _cartera()
    assert cartera[proximo.id_evento].semaforo == "PROXIMA" and cartera[proximo.id_evento].dias_para_evento == 5
    assert cartera[vigente.id_evento].semaforo == "VIGENTE"
    assert cartera[vencido.id_evento].semaforo == "VENCIDA" and cartera[vencido.id_evento].plazo == "Hace 3 días"


@pytest.mark.parametrize("dias, esperado", [(-1, "VENCIDA"), (0, "PROXIMA"), (21, "PROXIMA"), (22, "VIGENTE")])
def test_cp16_bordes_del_corte_de_21_dias(crear_usuario, dias, esperado):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    evento = _evento_a(id_cliente, dias)
    assert _cartera()[evento.id_evento].semaforo == esperado


def test_cp16_solo_cuentas_no_liquidadas_de_compromisos_firmes(crear_usuario):
    """Entran confirmados y realizados con saldo; no entran cotizaciones, cancelados ni liquidados (D-14)."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    confirmado = _evento_a(id_cliente, 10, abono=1000)
    realizado = _evento_a(id_cliente, -8, estado="REALIZADO")
    cotizacion = _evento_a(id_cliente, 10, estado="COTIZACION")
    cancelado = _evento_a(id_cliente, 10, estado="CANCELADO")
    liquidado = _evento_a(id_cliente, 12)
    with BaseDatos.transaccion() as cur:
        cur.execute("SELECT fn_registrar_pago(%s, %s, 'EFECTIVO')", (liquidado.id_evento, liquidado.costo_total))

    cartera = _cartera()
    assert cartera[confirmado.id_evento].saldo == confirmado.costo_total - 1000
    assert cartera[realizado.id_evento].semaforo == "VENCIDA"
    for fuera in (cotizacion, cancelado, liquidado):
        assert fuera.id_evento not in cartera


def test_cp16_total_adeudado_por_categoria(crear_usuario):
    """RF-37: cuentas y adeudo por categoría, calculados en la vista IB-08."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    antes = _totales()
    vencido = _evento_a(id_cliente, -2, abono=500)
    proximo = _evento_a(id_cliente, 3)
    despues = _totales()

    def delta(categoria, campo):
        return despues[categoria][campo] - antes.get(categoria, {}).get(campo, 0)

    assert delta("VENCIDA", "cuentas") == 1 and delta("VENCIDA", "adeudo") == vencido.costo_total - 500
    assert delta("PROXIMA", "cuentas") == 1 and delta("PROXIMA", "adeudo") == proximo.costo_total
    assert despues.get("VIGENTE", {}).get("cuentas", 0) == antes.get("VIGENTE", {}).get("cuentas", 0)


def test_cp16_pantalla_de_cartera(cliente_http, gerente, crear_usuario):
    """IU-08: tres totales por categoría, semáforo por cuenta y filtro por categoría."""
    id_cliente, correo, _ = crear_usuario("CLIENTE")
    vencido = _evento_a(id_cliente, -4, abono=2000)
    vigente = _evento_a(id_cliente, 60)

    texto = cliente_http.get("/reportes/cartera").get_data(as_text=True)
    assert all(t in texto for t in ("Vencida", "Próxima a vencer", "Vigente", "Total por cobrar"))
    fila = _fila(texto, vencido)
    assert 'etiqueta--roja">Vencida' in fila and "Hace 4 días" in fila and correo in fila
    assert f"${vencido.costo_total - 2000:,.2f}" in fila and "$2,000.00" in fila
    assert 'etiqueta--verde">Vigente' in _fila(texto, vigente)

    totales = _totales()
    assert f"${totales['VENCIDA']['adeudo']:,.2f}" in texto                # misma cifra que la vista

    solo_vencidas = cliente_http.get("/reportes/cartera?semaforo=VENCIDA").get_data(as_text=True)
    assert _fila(solo_vencidas, vencido) and _fila(solo_vencidas, vigente) is None
    assert '<option value="VENCIDA" selected>' in solo_vencidas
    assert _fila(cliente_http.get("/reportes/cartera?semaforo=NO_EXISTE").get_data(as_text=True), vigente)


def test_tablero_y_reporte_muestran_la_misma_cartera(cliente_http, gerente, crear_usuario):
    """SDD IU-08: el tablero toma lo vencido y lo que vence en 21 días de la misma vista IB-08."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    _evento_a(id_cliente, -6)
    _evento_a(id_cliente, 7)
    totales = _totales()
    panel = cliente_http.get("/panel").get_data(as_text=True)

    por_cobrar = sum(t["adeudo"] for t in totales.values())
    assert f"<strong>${por_cobrar:,.2f}</strong> por cobrar" in panel
    assert f"{totales['VENCIDA']['cuentas']} cuentas vencidas" in panel
    assert f"${totales['VENCIDA']['adeudo']:,.2f}" in panel and f"${totales['PROXIMA']['adeudo']:,.2f}" in panel
    assert 'href="/reportes/cartera?semaforo=VENCIDA"' in panel and 'href="/reportes/cartera?semaforo=PROXIMA"' in panel
    assert re.search(r'href="/reportes/cartera"[^>]*>Reportes</a>', panel)           # navegación


# ------------------------------ CP-17 ------------------------------
def test_cp17_activos_lista_cotizacion_y_confirmados_por_fecha(cliente_http, gerente, crear_usuario):
    """RF-35: solo cotización y confirmados, ordenados por fecha, con cliente, salón, paquete, aforo, costo y saldo."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    lejano = _evento_a(id_cliente, 3050, estado="COTIZACION", id_salon=3)
    cercano = _evento_a(id_cliente, 3040, abono=1500, id_salon=3)
    realizado = _evento_a(id_cliente, -9, estado="REALIZADO")
    cancelado = _evento_a(id_cliente, 3045, estado="CANCELADO")

    texto = cliente_http.get("/reportes/activos").get_data(as_text=True)
    assert _fila(texto, realizado) is None and _fila(texto, cancelado) is None
    assert texto.index(f'/eventos/{cercano.id_evento}"') < texto.index(f'/eventos/{lejano.id_evento}"')

    fila = _fila(texto, cercano)
    for dato in ("Prueba CLIENTE", "Terraza", "Paquete Clásico", "40 de 90", f"{cercano.fecha_evento:%d/%m/%Y}",
                 f"${cercano.costo_total:,.2f}", f"${cercano.costo_total - 1500:,.2f}", 'etiqueta--verde">Confirmado'):
        assert dato in fila, dato
    assert 'etiqueta--marino">Cotización' in _fila(texto, lejano)

    with BaseDatos.transaccion() as cur:
        fechas = [e.fecha_evento for e in RepositorioReportes(cur).activos()]
    assert fechas == sorted(fechas)

    solo_cotizacion = cliente_http.get("/reportes/activos?estado=COTIZACION&salon=3").get_data(as_text=True)
    assert _fila(solo_cotizacion, lejano) and _fila(solo_cotizacion, cercano) is None
    otro_salon = cliente_http.get("/reportes/activos?salon=2").get_data(as_text=True)
    assert _fila(otro_salon, lejano) is None


def test_cp17_realizados_muestra_costo_pagado_y_saldo(cliente_http, gerente, crear_usuario):
    """RF-36: solo eventos realizados, cada uno con costo, pagado y saldo restante."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    con_saldo = _evento_a(id_cliente, -15, estado="REALIZADO", abono=4000)
    liquidado = _evento_a(id_cliente, -20, estado="REALIZADO")
    with BaseDatos.transaccion() as cur:
        cur.execute("SELECT fn_registrar_pago(%s, %s, 'EFECTIVO')", (liquidado.id_evento, liquidado.costo_total))
    confirmado = _evento_a(id_cliente, -15)                      # pasó pero nadie lo cerró (RN-14)

    texto = cliente_http.get("/reportes/realizados").get_data(as_text=True)
    assert _fila(texto, confirmado) is None
    fila = _fila(texto, con_saldo)
    assert all(d in fila for d in (f"${con_saldo.costo_total:,.2f}", "$4,000.00",
                                   f"${con_saldo.costo_total - 4000:,.2f}", 'etiqueta--ambar">Con saldo'))
    fila = _fila(texto, liquidado)
    assert "$0.00" in fila and 'etiqueta--verde">Finiquitado' in fila
    assert texto.index(f'/eventos/{con_saldo.id_evento}"') < texto.index(f'/eventos/{liquidado.id_evento}"')   # reciente primero

    hoy = _hoy()
    rango = f"desde={hoy - timedelta(days=17):%Y-%m-%d}&hasta={hoy - timedelta(days=10):%Y-%m-%d}"
    en_rango = cliente_http.get(f"/reportes/realizados?{rango}").get_data(as_text=True)
    assert _fila(en_rango, con_saldo) and _fila(en_rango, liquidado) is None
    finiquitados = cliente_http.get("/reportes/realizados?liquidacion=FINIQUITADO").get_data(as_text=True)
    assert _fila(finiquitados, liquidado) and _fila(finiquitados, con_saldo) is None


def test_realizados_rechaza_un_rango_invertido_o_una_fecha_mal_escrita(cliente_http, gerente):
    invertido = cliente_http.get("/reportes/realizados?desde=2026-12-31&hasta=2026-01-01")
    assert invertido.status_code == 200 and "no puede ser posterior" in invertido.get_data(as_text=True)
    mala = cliente_http.get("/reportes/realizados?desde=ayer")
    assert mala.status_code == 200 and "debe ser una fecha válida" in mala.get_data(as_text=True)


# ------------------------------ CP-18 ------------------------------
@pytest.mark.parametrize("reporte", ["cartera", "activos", "realizados"])
def test_cp18_csv_con_las_mismas_columnas_de_la_pantalla(cliente_http, gerente, crear_usuario, reporte):
    """RF-38 · IE-02: mismas columnas y mismos renglones que la pantalla, en UTF-8 y separado por comas."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    _evento_a(id_cliente, 9, nombre="Boda Ñandú")
    _evento_a(id_cliente, -11, estado="REALIZADO", abono=700)

    pantalla = cliente_http.get(f"/reportes/{reporte}").get_data(as_text=True)
    assert f'href="/reportes/{reporte}?formato=csv"' in pantalla
    descarga = cliente_http.get(f"/reportes/{reporte}?formato=csv")

    assert descarga.status_code == 200
    assert descarga.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert re.fullmatch(rf'attachment; filename="{reporte}_\d{{4}}-\d{{2}}-\d{{2}}\.csv"',
                        descarga.headers["Content-Disposition"])
    assert descarga.get_data().startswith(b"\xef\xbb\xbf")               # UTF-8 que Excel reconoce
    filas = _csv(descarga)
    assert filas[0] == _encabezados(pantalla)                              # mismas columnas, mismo orden
    assert len(filas) - 1 == pantalla.count('<th scope="row"')             # mismos renglones
    assert all(len(f) == len(filas[0]) for f in filas)


def test_cp18_el_csv_trae_los_mismos_datos_y_respeta_el_filtro(cliente_http, gerente, crear_usuario):
    id_cliente, correo, _ = crear_usuario("CLIENTE")
    vencido = _evento_a(id_cliente, -5, abono=1234.5)
    vigente = _evento_a(id_cliente, 90)

    filas = _csv(cliente_http.get("/reportes/cartera?semaforo=VENCIDA&formato=csv"))
    por_clave = {f[0]: dict(zip(filas[0], f)) for f in filas[1:]}
    assert vigente.clave_proyecto not in por_clave
    fila = por_clave[vencido.clave_proyecto]
    assert fila["Cliente"] == "Prueba CLIENTE" and fila["Contacto"] == correo and fila["Salón"] == "Salón Principal"
    assert fila["Fecha del evento"] == f"{vencido.fecha_evento:%d/%m/%Y}" and fila["Plazo"] == "Hace 5 días"
    assert fila["Pagado"] == "1234.50" and Decimal(fila["Saldo"]) == vencido.costo_total - Decimal("1234.50")
    assert fila["Semáforo"] == "Vencida"
    assert all(f[-1] == "Vencida" for f in filas[1:])


def test_cp18_el_csv_no_ejecuta_formulas(cliente_http, gerente, crear_usuario):
    """Un nombre que empieza con = se entrega como texto, no como fórmula de la hoja de cálculo."""
    from app.datos.repositorio_usuarios import RepositorioUsuarios
    from app.seguridad import claves
    from tests.conftest import correo_unico
    with BaseDatos.transaccion() as cur:
        id_cliente = RepositorioUsuarios(cur).insertar('=HYPERLINK("http://x")', correo_unico(), None,
                                                       "CLIENTE", claves.cifrar("Inicial-1"))
    evento = _evento_a(id_cliente, 4)
    filas = _csv(cliente_http.get("/reportes/cartera?formato=csv"))
    fila = next(f for f in filas if f[0] == evento.clave_proyecto)
    assert fila[1] == '\'=HYPERLINK("http://x")'


def test_la_descarga_queda_en_bitacora(cliente_http, gerente):
    cliente_http.get("/reportes/activos?formato=csv")
    with BaseDatos.transaccion() as cur:
        cur.execute("""SELECT entidad FROM bitacora WHERE id_usuario = %s AND accion = 'DESCARGA_REPORTE'""", (gerente,))
        assert [f["entidad"] for f in cur.fetchall()] == ["reporte:activos"]
    cliente_http.get("/reportes/activos")                                   # ver en pantalla no se registra
    with BaseDatos.transaccion() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM bitacora WHERE id_usuario = %s", (gerente,))
        assert cur.fetchone()["n"] == 2                                      # inicio de sesión + descarga


# ---------------------------- acceso y vacío ----------------------------
def test_rf05_cliente_no_entra_a_reportes(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("CLIENTE")
    _entrar(cliente_http, correo, clave)
    for ruta in ("/reportes", "/reportes/cartera", "/reportes/activos", "/reportes/realizados",
                 "/reportes/cartera?formato=csv"):
        respuesta = cliente_http.get(ruta)
        assert respuesta.status_code == 302 and respuesta.location.endswith("/mis-eventos"), ruta
    assert "Reportes" not in cliente_http.get("/mis-eventos").get_data(as_text=True)


def test_sin_sesion_no_hay_reportes(cliente_http):
    for ruta in ("/reportes/cartera", "/reportes/activos?formato=csv"):
        respuesta = cliente_http.get(ruta)
        assert respuesta.status_code == 302 and "/login" in respuesta.location


def test_reportes_abre_en_cartera(cliente_http, gerente):
    respuesta = cliente_http.get("/reportes")
    assert respuesta.status_code == 302 and respuesta.location.endswith("/reportes/cartera")


def test_filtro_sin_resultados_ofrece_quitarlo(cliente_http, gerente):
    texto = cliente_http.get("/reportes/realizados?desde=1990-01-01&hasta=1990-01-02").get_data(as_text=True)
    assert "Ningún registro coincide con los filtros" in texto and "Descargar CSV" not in texto


def test_activos_sin_saldo_en_cotizaciones(cliente_http, gerente, crear_usuario):
    """DESIGN.md «Dinero por estatus»: en Activos una cotización no muestra saldo, ni en pantalla ni en el CSV."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    cotizacion = _evento_a(id_cliente, 3061, estado="COTIZACION", id_salon=2)
    fila = _fila(cliente_http.get("/reportes/activos").get_data(as_text=True), cotizacion)
    saldo = fila.split('data-etiqueta="Saldo"')[1].split("</td>")[0]
    assert "—" in saldo and "$" not in saldo
    filas = _csv(cliente_http.get("/reportes/activos?formato=csv"))
    columnas = filas[0]
    propia = next(f for f in filas[1:] if f[columnas.index("Clave")] == cotizacion.clave_proyecto)
    assert propia[columnas.index("Saldo")] == ""

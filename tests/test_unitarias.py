"""Pruebas unitarias (sin base de datos) · RNF-04 · RNF-14 · RF-01 · RN-06/07."""
from decimal import Decimal

import pytest

from app.datos.errores import ErrorValidacion
from app.dominio.modelos import Platillo, agrupar_por_categoria
from app.rutas.acceso import _destino_seguro
from app.seguridad import claves
from app.servicios.validaciones import (entero_positivo, importe,
                                        interpretar_identificador,
                                        normalizar_correo, normalizar_telefono)


class TestClaves:
    def test_clave_legible_formato_y_alfabeto(self):            # RNF-14
        for _ in range(200):
            clave = claves.generar_clave_legible()
            assert len(clave) == 9 and clave[4] == "-"
            assert all(c in claves.ALFABETO_DICTABLE for c in clave.replace("-", ""))
            assert not set("0O1IL") & set(clave)

    def test_cifrado_con_sal(self):                               # RNF-04
        h1, h2 = claves.cifrar("MiClave123"), claves.cifrar("MiClave123")
        assert h1 != h2                     # sal distinta en cada hash
        assert "MiClave123" not in h1
        assert claves.verificar(h1, "MiClave123")
        assert not claves.verificar(h1, "otra")

    @pytest.mark.parametrize("escrita", ["k7pm-3qxr", "K7PM3QXR", "k7pm 3qxr", " K7PM-3QXR "])
    def test_clave_inicial_tolerante_al_dictado(self, escrita):
        assert claves.normalizar_clave_inicial(escrita) == "K7PM-3QXR"

    def test_condiciones_clave_nueva(self):                       # IU-02, Figura 28
        assert claves.errores_clave_nueva("Segura2026", "Segura2026", "ABCD-EFGH") == []
        assert len(claves.errores_clave_nueva("abc", "xyz")) == 2           # corta y no coincide
        assert claves.errores_clave_nueva("ABCD-EFGH", "ABCD-EFGH", "ABCD-EFGH") == [
            "La clave nueva debe ser distinta de la actual."]

    @pytest.mark.parametrize("destino, esperado", [
        ("/clientes?q=ana", "/clientes?q=ana"),
        ("//evil.com", None), ("/\\evil.com", None), ("/\t/evil.com", None),
        ("https://evil.com", None), ("", None), (None, None),
    ])
    def test_destino_seguro_tras_login(self, destino, esperado):   # redirección abierta
        assert _destino_seguro(destino) == esperado


class TestValidaciones:
    @pytest.mark.parametrize("entrada", ["4921234567", "492 123 4567", "(492) 123-4567", "+52 492 123 4567"])
    def test_telefono_normalizado(self, entrada):
        assert normalizar_telefono(entrada) == "4921234567"

    def test_telefono_invalido(self):
        with pytest.raises(ErrorValidacion):
            normalizar_telefono("12345")

    def test_correo_en_minusculas(self):
        assert normalizar_correo("  Ana.Lopez@Mail.COM ") == "ana.lopez@mail.com"

    def test_correo_invalido(self):
        with pytest.raises(ErrorValidacion):
            normalizar_correo("ana@")

    def test_un_solo_campo_acepta_correo_o_celular(self):        # RF-01
        assert interpretar_identificador("Ana@Mail.com") == ("correo", "ana@mail.com")
        assert interpretar_identificador("492-123-4567") == ("telefono", "4921234567")


class TestImportes:
    def test_importe_valido(self):
        assert importe("$19,500.5", "Costo") == Decimal("19500.50")

    @pytest.mark.parametrize("texto", ["NaN", "Infinity", "abc", "-1", "100000000"])
    def test_importe_invalido_no_truena(self, texto):           # antes "NaN" daba error 500
        with pytest.raises(ErrorValidacion):
            importe(texto, "Precio")

    @pytest.mark.parametrize("texto", ["0", "x", "3000000000"])
    def test_entero_fuera_de_rango(self, texto):
        with pytest.raises(ErrorValidacion):
            entero_positivo(texto, "Capacidad")


class TestDominio:
    def test_agrupacion_respeta_orden_de_categorias(self):        # RF-17
        platillos = [Platillo(1, "Flan", "POSTRE"), Platillo(2, "Sopa", "ENTRADA"),
                     Platillo(3, "Agua", "BEBIDA")]
        assert list(agrupar_por_categoria(platillos)) == ["ENTRADA", "POSTRE", "BEBIDA"]

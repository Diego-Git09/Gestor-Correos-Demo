import importlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from gestor_correos import demostracion as demo


class DemostracionTests(unittest.TestCase):
    def test_lote_con_correo_y_sin_correo_no_envia_nada(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('La demo no necesita red')):
            resultados = demo.preparar_demostracion(demo.cargar_ejemplos())
        self.assertEqual(demo.resumen(resultados), {'total': 3, 'simulados': 2, 'omitidos': 1, 'envios_reales': 0})
        self.assertIn('Ana', resultados[0].cuerpo)
        self.assertNotIn('{cliente}', resultados[0].asunto)

    def test_un_correo_real_rechaza_el_lote_completo(self):
        filas = demo.cargar_ejemplos()
        filas[-1]['Correo'] = 'persona@example.com'
        with self.assertRaisesRegex(ValueError, 'ficticias'):
            demo.preparar_demostracion(filas)

    def test_variables_desconocidas_no_generan_resultados(self):
        with self.assertRaisesRegex(ValueError, 'Variables desconocidas'):
            demo.preparar_demostracion(demo.cargar_ejemplos(), asunto='{contraseña}')

    def test_campana_vacia_y_mensaje_vacio_son_errores(self):
        with self.assertRaisesRegex(ValueError, 'contacto'):
            demo.preparar_demostracion([])
        with self.assertRaisesRegex(ValueError, 'vacíos'):
            demo.preparar_demostracion(demo.cargar_ejemplos(), cuerpo='  ')

    def test_reporte_refleja_simulacion_y_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / 'reporte.json'
            datos = demo.preparar_demostracion(demo.cargar_ejemplos())
            demo.exportar_reporte(archivo, datos)
            contenido = archivo.read_bytes()
            self.assertEqual(json.loads(contenido)['resumen']['envios_reales'], 0)
            with self.assertRaises(FileExistsError):
                demo.exportar_reporte(archivo, [])
            self.assertEqual(archivo.read_bytes(), contenido)

    def test_pdf_real_se_valida_sin_modificarlo(self):
        from pypdf import PdfWriter
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / 'catalogo_demo.pdf'
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            with pdf.open('wb') as stream:
                writer.write(stream)
            antes = pdf.read_bytes()
            resultados = demo.preparar_demostracion(demo.cargar_ejemplos(), pdf=pdf)
            self.assertEqual(resultados[0].adjunto, 'catalogo_demo.pdf')
            self.assertEqual(pdf.read_bytes(), antes)

    def test_pdf_falso_y_cifrado_se_rechazan(self):
        from pypdf import PdfWriter
        with tempfile.TemporaryDirectory() as tmp:
            falso = Path(tmp) / 'falso.pdf'
            falso.write_text('Este archivo no es un PDF.')
            with self.assertRaises(ValueError):
                demo.comprobar_pdf(falso)
            pdf = Path(tmp) / 'cifrado.pdf'
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            writer.encrypt('clave-ficticia')
            with pdf.open('wb') as stream:
                writer.write(stream)
            with self.assertRaisesRegex(ValueError, 'cifrados'):
                demo.comprobar_pdf(pdf)

    def test_entrada_cli_ejecuta_lote_de_demostracion(self):
        root = Path(__file__).resolve().parents[1]
        proceso = subprocess.run([sys.executable, '-B', str(root / 'main.py'), '--demo-cli'], capture_output=True, text=True, timeout=20, cwd=root)
        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        self.assertEqual(json.loads(proceso.stdout)['envios_reales'], 0)


@unittest.skipUnless(all(importlib.util.find_spec(n) for n in ('selenium', 'keyring', 'cryptography')), 'Instala requirements-desarrollo.txt para comprobar los módulos históricos.')
class IntegracionesBloqueadasTests(unittest.TestCase):
    def test_bloqueos_antes_de_abrir_cuentas_navegadores_o_enviar(self):
        casos = [
            ('navegador', 'crear_driver', ('perfil-demo', False, 'driver-demo')),
            ('navegador', 'cerrar_sesion_gmail', ()),
            ('credenciales', 'recuperar_credenciales', ()),
            ('crm', 'login_crm', (None, 'ficticio', 'ficticio')),
            ('crm', 'registrar_gestion_crm', (None, None, 'demo')),
        ]
        with patch.object(socket, 'socket', side_effect=AssertionError('Sin red')):
            for modulo, nombre, args in casos:
                with self.subTest(funcion=nombre):
                    funcion = getattr(importlib.import_module('gestor_correos.' + modulo), nombre)
                    with self.assertRaisesRegex(RuntimeError, 'deshabilitada'):
                        funcion(*args)


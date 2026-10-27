import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
from gestor_correos import adaptadores_demo as a, configuracion as c, eventos


class AdaptadoresTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        raiz = Path(self.tmp.name)
        p = patch.multiple(c, BASE_DIR=str(raiz), CONTACTOS_FILE=str(raiz/'contactos.json'))
        p.start()
        self.addCleanup(p.stop)
        a.preparar_entorno()
        eventos.DETENER.clear()

    def test_false_en_dry_run_tambien_simula_sin_red(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('Sin red')):
            resultados, reporte = a.ejecutar_campana('demo', 'ficticio', 1, 3, '', False, 'Hola {nombre}', 'Texto {cliente}', 'Demo', dry_run=False)
        self.assertEqual(json.loads(reporte.read_text())['resumen']['envios_reales'], 0)
        self.assertEqual(len(resultados), 3)

    def test_identidad_no_lee_ni_guarda_secretos(self):
        with patch.dict('os.environ', {'Demo_MANAGER_USER': 'no-utilizar', 'Demo_MANAGER_PASSWORD': 'no-utilizar'}):
            self.assertEqual(a.credenciales_manager_desde_entorno()['user'], 'demo-local')
            self.assertIsNone(a.recuperar_credenciales())
            self.assertTrue(a.guardar_identidad('nombre', 'clave', True, 'persona'))
        self.assertFalse(Path(c.BASE_DIR, 'bot_config.json').exists())

    def test_detener_produce_reporte_sin_contactos_procesados(self):
        eventos.DETENER.set()
        resultados, reporte = a.ejecutar_campana('demo', 'ficticio', 1, 3, '', False, 'Hola {nombre}', 'Texto {cliente}', 'Demo')
        self.assertEqual(resultados, [])
        self.assertEqual(json.loads(reporte.read_text())['resumen']['total'], 0)

"""Resultados de referencia obtenidos de funciones puras del archivo original."""
import json
from pathlib import Path
import unittest
from gestor_correos import validacion, utilidades, plantillas, contactos
MODULOS = {'normalizar_id':validacion,'primer_nombre':validacion,'normalizar_correo':validacion,'sanitizar_texto':utilidades,'renderizar_plantilla':plantillas,'variables_desconocidas':plantillas,'deduplicar_contactos':contactos,'formatear_duracion':utilidades}
class EquivalenciaTests(unittest.TestCase):
    def test_comportamiento_original_en_entradas_ficticias(self):
        casos=json.loads(Path(__file__).with_name('casos_originales.json').read_text())
        for caso in casos:
            with self.subTest(funcion=caso['funcion'], argumentos=caso['argumentos']):
                funcion=getattr(MODULOS[caso['funcion']],caso['funcion'])
                self.assertEqual(funcion(*caso['argumentos']),caso['esperado'])

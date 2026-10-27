import os
import socket
import tkinter as tk
import unittest
from unittest.mock import patch

from gestor_correos.interfaz_demo import AplicacionDemo


@unittest.skipUnless(os.environ.get('GESTOR_UI_REAL') == '1', 'Activa GESTOR_UI_REAL=1 en una sesión gráfica.')
class InterfazTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = AplicacionDemo(self.root)
        self.root.update_idletasks()

    def test_vista_previa_y_simulacion_sin_red(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('Sin red')):
            self.app.vista_previa()
            self.assertIn('Ana', self.app.salida.get('1.0', 'end'))
            self.app.simular()
        self.assertIn('2 simulados', self.app.estado.cget('text'))
        self.assertEqual(str(self.app.exportar.cget('state')), 'normal')
        self.assertEqual(self.app.tabla.set('3', 'estado'), 'OMITIDO_SIN_CORREO')

    def test_sin_seleccion_muestra_error_y_no_produce_resultados(self):
        self.app.tabla.selection_remove(self.app.tabla.selection())
        with patch('gestor_correos.interfaz_demo.messagebox.showerror') as aviso:
            self.app.simular()
        aviso.assert_called_once()
        self.assertEqual(self.app.resultados, [])


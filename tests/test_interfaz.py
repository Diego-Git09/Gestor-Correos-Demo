import json
import os
from pathlib import Path
import socket
import tempfile
import time
import unittest
from unittest.mock import patch

import customtkinter as ctk
from gestor_correos import configuracion, eventos
from gestor_correos.interfaz_demo import AplicacionDemo


@unittest.skipUnless(os.environ.get('GESTOR_UI_REAL') == '1', 'Activa GESTOR_UI_REAL=1 en una sesión gráfica.')
class InterfazTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        raiz = Path(self.tmp.name)
        paths = patch.multiple(configuracion, BASE_DIR=str(raiz), CONFIG_FILE=str(raiz/'bot_config.json'),
                               CONTACTOS_FILE=str(raiz/'contactos_sincronizados.json'), LOG_FILE=str(raiz/'reporte_envios_log.csv'))
        paths.start()
        self.addCleanup(paths.stop)
        while not eventos.COLA.empty():
            eventos.COLA.get_nowait()
        eventos.DETENER.clear()
        self.root = ctk.CTk()
        self.root.withdraw()
        self.addCleanup(self.cerrar)
        with patch.object(socket, 'socket', side_effect=AssertionError('El formulario no necesita red')):
            self.app = AplicacionDemo(self.root)
        self.root.update_idletasks()
        self.c = self.app.controles

    def cerrar(self):
        eventos.DETENER.set()
        p = getattr(self.root, 'gestor_progreso', None)
        if p is not None:
            p.hilo.join(timeout=3)
        for job in self.root.tk.call('after', 'info'):
            self.root.after_cancel(job)
        self.root.destroy()

    def esperar(self, condicion):
        limite = time.monotonic() + 5
        while time.monotonic() < limite:
            self.root.update()
            if condicion():
                return
            time.sleep(.015)
        self.fail('La interfaz no completó la operación a tiempo.')

    def test_diseno_original_y_cuentas_bloqueadas(self):
        self.assertTrue(self.c['prueba'].get())
        self.assertEqual(str(self.c['usuario'].cget('state')), 'disabled')
        self.assertEqual(str(self.c['password'].cget('state')), 'disabled')
        self.assertEqual(self.c['inicio'].get(), '1')
        self.assertEqual(self.c['fin'].get(), '3')
        self.assertIn('MAILBOT', self.textos())
        self.assertIn('RANGO DE CONTACTOS', self.textos())
        self.assertIn('MENSAJE', self.textos())

    def textos(self):
        textos = []
        def recorrer(widget):
            try:
                textos.append(str(widget.cget('text')))
            except Exception:
                pass
            for hijo in widget.winfo_children():
                recorrer(hijo)
        recorrer(self.root)
        return ' '.join(textos)

    def test_vista_previa_usa_el_formulario_original(self):
        self.c['asunto'].set('Mensaje para {nombre}')
        with patch('gestor_correos.formulario.messagebox.showinfo') as aviso:
            self.app.vista_previa()
        self.assertIn('Mensaje para Carlos', aviso.call_args.args[1])

    def test_formulario_progreso_y_reporte_sin_red(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('Sin red')), \
             patch('gestor_correos.formulario.messagebox.askyesno', return_value=True), \
             patch('gestor_correos.progreso.messagebox.showerror') as error:
            self.app.simular()
            self.esperar(lambda: hasattr(self.root, 'gestor_progreso') and self.root.gestor_progreso.terminado)
        progreso = self.root.gestor_progreso
        error.assert_not_called()
        self.assertEqual(progreso.stat_labels['enviados'].cget('text'), '2')
        self.assertIn('SIMULADOS', self.textos())
        self.assertEqual(len(progreso.resultados), 3)
        datos = json.loads(progreso.reporte_demo.read_text())
        self.assertEqual(datos['resumen'], {'total': 3, 'simulados': 2, 'omitidos': 1, 'envios_reales': 0})

    def test_rango_invalido_no_abre_progreso(self):
        self.c['inicio'].delete(0, 'end')
        self.c['inicio'].insert(0, '9')
        with patch('gestor_correos.formulario.messagebox.showerror') as error:
            self.app.simular()
        error.assert_called_once()
        self.assertFalse(hasattr(self.root, 'gestor_progreso'))

    def test_cargar_base_solo_utiliza_ejemplos_locales(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('Sin red')), \
             patch('gestor_correos.formulario.messagebox.showinfo') as aviso:
            self.c['sincronizar']()
            self.esperar(lambda: aviso.called)
        self.assertIn('3 contactos', self.c['base'].cget('text'))
        contactos = json.loads(Path(configuracion.CONTACTOS_FILE).read_text())['contactos']
        self.assertTrue(all(not c['Correo'] or c['Correo'].endswith('@example.invalid') for c in contactos))

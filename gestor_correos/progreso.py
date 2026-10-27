"""Progreso: código separado del archivo original; versión de demostración."""
import os
import sys
import queue
import threading
import traceback
import subprocess
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from . import automatizacion as _automatizacion
from . import configuracion as _configuracion
from . import eventos as _eventos
from . import imagenes as _imagenes
from . import tema as _tema
from . import utilidades as _utilidades


class VentanaProgreso:
    FICHAS = (('enviados', 'Enviados', _tema.VERDE), ('errores', 'Fallidos', _tema.ROJO), ('omitidos', 'Omitidos', _tema.APAGADO), ('pendientes', 'Pendientes', _tema.AMBAR), ('sin_correo', 'Sin correo', _tema.VIOLETA))

    def __init__(self, root, args):
        self.root = root
        self.terminado = False
        self.cerrar_pendiente = False
        for w in root.winfo_children():
            w.destroy()
        root.title('Automatización Correos - Iniciando...')
        root.geometry('780x640')
        root.minsize(620, 460)
        root.resizable(True, True)
        cab = ttk.Frame(root, padding=(22, 16, 22, 6))
        cab.pack(fill='x')
        ttk.Label(cab, text='PROCESO EN CURSO', style='Muted.TLabel').pack(anchor='w')
        self.lbl_estado = ttk.Label(cab, text='Iniciando...', style='Estado.TLabel', wraplength=720)
        self.lbl_estado.pack(anchor='w', pady=(2, 0))
        _tema.BarraNeon(root, 3).pack(fill='x', padx=22, pady=(4, 10))
        frame = ttk.Frame(root, padding=(22, 0, 22, 16))
        frame.pack(fill='both', expand=True)
        self.barra = ttk.Progressbar(frame, maximum=1, value=0, mode='determinate', style='Neon.Horizontal.TProgressbar')
        self.barra.pack(fill='x', pady=(0, 6))
        self.lbl_eta = ttk.Label(frame, text='', style='Eta.TLabel')
        self.lbl_eta.pack(anchor='w', pady=(0, 10))
        fila_fichas = ttk.Frame(frame)
        fila_fichas.pack(fill='x', pady=(0, 12))
        self.stat_labels = {}
        for i, (clave, titulo, color) in enumerate(self.FICHAS):
            fila_fichas.columnconfigure(i, weight=1, uniform='fichas')
            ficha, valor = _tema.ficha_stat(fila_fichas, titulo, color)
            ficha.grid(row=0, column=i, sticky='ew', padx=(0 if i == 0 else 4, 0 if i == len(self.FICHAS) - 1 else 4))
            self.stat_labels[clave] = valor
        cont = tk.Frame(frame, bg=_tema.LOG_BG, highlightthickness=1, highlightbackground=_tema.BORDE)
        cont.pack(fill='both', expand=True)
        hay_pillow = _imagenes.pillow_disponible() and os.path.exists(_configuracion.LOGO_FILE)
        self.logo_img = None
        if not hay_pillow:
            self.logo_img = _imagenes.cargar_logo_chico()
            if self.logo_img is not None:
                tk.Label(cont, image=self.logo_img, bg=_tema.LOG_BG).pack(side='top', pady=(6, 2))
        self.log = _imagenes.LogCanvas(cont, (_tema.FUENTE_MONO, 9 if _configuracion.ES_WINDOWS else 10), con_logo=hay_pillow)
        sb = ttk.Scrollbar(cont, command=self.log.mover_barra)
        self.log.sb = sb
        sb.pack(side='right', fill='y')
        self.log.pack(side='left', fill='both', expand=True)
        self.barra_botones = ttk.Frame(frame)
        self.barra_botones.pack(fill='x', pady=(12, 0))
        self.btn = ttk.Button(self.barra_botones, text='⏹  Detener (termina el contacto actual)', style='Danger.TButton', command=self.detener)
        self.btn.pack(side='right')
        root.protocol('WM_DELETE_WINDOW', self.al_cerrar)
        self.hilo = threading.Thread(target=self._trabajo, args=args, daemon=True)
        self.hilo.start()
        root.after(150, self.procesar_cola)

    def _trabajo(self, *args):
        ruta_ejecucion = os.path.join(_configuracion.BASE_DIR, 'logs_ejecucion', f'ejecucion_{datetime.now():%Y-%m-%d}.log')
        escritor = _eventos.EscritorCola(_eventos.COLA, ruta_ejecucion)
        salida_original, error_original = (sys.stdout, sys.stderr)
        sys.stdout = escritor
        sys.stderr = escritor
        try:
            _automatizacion.ejecutar_bot(*args)
        except Exception:
            print('❌ Error inesperado:\n' + traceback.format_exc())
            _eventos.ui_aviso('error', 'Error inesperado', 'El bot se detuvo por un error. El detalle está en la ventana de progreso.')
        finally:
            escritor.vaciar()
            sys.stdout, sys.stderr = (salida_original, error_original)
            _eventos.COLA.put(('fin',))

    def detener(self):
        _eventos.DETENER.set()
        self.btn.config(state='disabled', text='Deteniendo...')
        self.lbl_estado.config(text='Deteniendo: termina el contacto actual...')

    def al_cerrar(self):
        if self.terminado or not self.hilo.is_alive():
            self.root.destroy()
            return
        if messagebox.askyesno('Bot en ejecución', 'El bot sigue trabajando.\n\nPara ocultar la ventana sin detenerlo, minimízala.\n\n¿Quieres detenerlo y cerrar? (termina el contacto actual antes de cerrarse)'):
            self.cerrar_pendiente = True
            self.detener()

    def agregar(self, linea):
        linea = ''.join((c if ord(c) <= 65535 else '▸' for c in linea))
        tag = None
        if '❌' in linea:
            tag = 'error'
        elif '⚠' in linea:
            tag = 'aviso'
        elif '✓' in linea:
            tag = 'ok'
        elif '⚙' in linea:
            tag = 'debug'
        self.log.agregar(linea, tag)

    def actualizar_stats(self, s):
        for clave, etiqueta in self.stat_labels.items():
            etiqueta.config(text=str(s.get(clave, 0)))

    def procesar_cola(self):
        try:
            while True:
                msg = _eventos.COLA.get_nowait()
                try:
                    self._manejar_mensaje(msg)
                except Exception:
                    self.agregar('❌ Error en la interfaz:\n' + traceback.format_exc())
                if msg[0] == 'fin':
                    return
        except queue.Empty:
            pass
        if not self.hilo.is_alive() and (not self.terminado):
            self.al_terminar()
            return
        self.root.after(150, self.procesar_cola)

    def _manejar_mensaje(self, msg):
        tipo = msg[0]
        if tipo == 'log':
            self.agregar(msg[1])
        elif tipo == 'progreso':
            _, hechos, total, texto = msg
            self.barra.config(maximum=max(total, 1), value=hechos)
            self.lbl_estado.config(text=texto)
            self.root.title(f'Bot Demo - {hechos}/{total}')
        elif tipo == 'stats':
            self.actualizar_stats(msg[1])
        elif tipo == 'eta':
            self.lbl_eta.config(text=msg[1])
        elif tipo == 'aviso':
            _, nivel, titulo, texto = msg
            mostrar = {'error': messagebox.showerror, 'warning': messagebox.showwarning}.get(nivel, messagebox.showinfo)
            mostrar(titulo, texto)
        elif tipo == 'fin_campana':
            self.notificar_fin_campana(msg[1], msg[2])
        elif tipo == 'problemas':
            self.mostrar_problemas(msg[1])
        elif tipo == 'fin':
            self.al_terminar()

    def traer_al_frente(self):
        """Eleva la ventana principal sobre el resto de aplicaciones (restaurándola si estaba minimizada)."""
        r = self.root
        try:
            if r.state() == 'iconic':
                r.iconify()
                r.deiconify()
            else:
                r.deiconify()
            r.lift()
            r.attributes('-topmost', True)
            r.update()
            r.focus_force()
        except tk.TclError as e:
            _utilidades.log_debug('traer ventana al frente', e)
        if _configuracion.ES_MAC:
            try:
                subprocess.call(['osascript', '-e', f'tell application "System Events" to set frontmost of the first process whose unix id is {os.getpid()} to true'], timeout=5)
            except Exception:
                pass

    def notificar_fin_campana(self, titulo, texto):
        """Aviso notorio y audible: ventana al frente + campana del sistema + resumen completo."""
        if self.cerrar_pendiente:
            return
        r = self.root
        self.traer_al_frente()
        try:
            r.bell()
        except tk.TclError:
            pass
        _tema.sonar_alerta(r)
        try:
            messagebox.showinfo(titulo, texto, parent=r)
        finally:
            try:
                r.attributes('-topmost', False)
            except tk.TclError:
                pass

    def al_terminar(self):
        if self.terminado:
            return
        self.terminado = True
        if self.cerrar_pendiente:
            self.root.destroy()
            return
        self.root.title('Automatización Correos - Terminado')
        self.btn.config(text='Cerrar', state='normal', style='Accent.TButton', command=self.root.destroy)
        carpeta_logs = os.path.join(_configuracion.BASE_DIR, 'logs_ejecucion')
        ttk.Button(self.barra_botones, text='📂  Abrir carpeta de logs', command=lambda: _utilidades.abrir_ruta(carpeta_logs if os.path.isdir(carpeta_logs) else _configuracion.BASE_DIR)).pack(side='left', padx=(0, 8))
        ttk.Button(self.barra_botones, text='📄  Abrir reporte', command=lambda: _utilidades.abrir_ruta(_configuracion.LOG_FILE if os.path.exists(_configuracion.LOG_FILE) else _configuracion.BASE_DIR)).pack(side='left')

    def mostrar_problemas(self, lista):
        if self.cerrar_pendiente:
            return
        win = tk.Toplevel(self.root)
        win.configure(bg=_tema.BG)
        win.title(f'Contactos a revisar ({len(lista)})')
        win.geometry('940x420')
        win.minsize(640, 280)
        win.transient(self.root)
        marco = ttk.Frame(win, padding=16)
        marco.pack(fill='both', expand=True)
        ttk.Label(marco, font=_tema.fuente_ui(10, 'bold'), wraplength=890, justify='left', foreground=_tema.AMBAR, text=f"{len(lista)} contacto(s) necesitan revisión manual. Revisa Gmail > Enviados en los REVISAR; en 'FALLÓ GESTIÓN' el correo sí salió y solo falta crear la gestión en el Manager.").pack(anchor='w', pady=(0, 10))
        columnas = ('id', 'nombre', 'cliente', 'estado', 'detalle')
        anchos = {'id': 70, 'nombre': 160, 'cliente': 220, 'estado': 190, 'detalle': 300}
        cont, tabla = _tema.crear_tabla(marco, columnas, anchos)
        cont.pack(fill='both', expand=True)
        for p in lista:
            tabla.insert('', 'end', tags=_tema.etiqueta_estado(p['estado']), values=(p['id'], p['nombre'], p['cliente'], p['estado'], p['detalle']))

        def copiar():
            filas = ['ID\tNombre\tCliente\tEstado\tDetalle']
            filas += [f"{p['id']}\t{p['nombre']}\t{p['cliente']}\t{p['estado']}\t{p['detalle']}" for p in lista]
            self.root.clipboard_clear()
            self.root.clipboard_append('\n'.join(filas))
        botones = ttk.Frame(marco)
        botones.pack(fill='x', pady=(10, 0))
        ttk.Button(botones, text='Cerrar', command=win.destroy).pack(side='right')
        ttk.Button(botones, text='📋  Copiar lista', style='Accent.TButton', command=copiar).pack(side='right', padx=8)

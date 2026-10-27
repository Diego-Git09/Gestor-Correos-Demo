"""Eventos: código separado del archivo original; versión de demostración."""
import os
import queue
import threading
from datetime import datetime, timedelta


_PERFILES_BLOQUEADOS = set()

COLA = queue.Queue()

DETENER = threading.Event()

class EscritorCola:

    def __init__(self, cola, ruta_archivo=None):
        self.cola = cola
        self.buf = ''
        self.archivo = None
        if ruta_archivo:
            try:
                os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
                self.archivo = open(ruta_archivo, 'a', encoding='utf-8')
            except OSError:
                self.archivo = None

    def _emitir(self, linea):
        self.cola.put(('log', linea))
        if self.archivo:
            try:
                self.archivo.write(f'{datetime.now():%H:%M:%S}  {linea}\n')
                self.archivo.flush()
            except Exception:
                self.archivo = None

    def write(self, s):
        self.buf += s
        while '\n' in self.buf:
            linea, self.buf = self.buf.split('\n', 1)
            self._emitir(linea)
        return len(s)

    def flush(self):
        pass

    def vaciar(self):
        if self.buf:
            self._emitir(self.buf)
            self.buf = ''
        if self.archivo:
            try:
                self.archivo.close()
            except Exception:
                pass
            self.archivo = None

def ui_progreso(hechos, total, texto):
    COLA.put(('progreso', hechos, total, texto))

def ui_stats(stats):
    COLA.put(('stats', dict(stats)))

def ui_aviso(nivel, titulo, texto):
    COLA.put(('aviso', nivel, titulo, texto))

def ui_fin_campana(titulo, texto):
    """Aviso final de campaña: la ventana principal se trae al frente, suena una campana y
    se muestra el resumen completo (ver VentanaProgreso.notificar_fin_campana)."""
    COLA.put(('fin_campana', titulo, texto))

def ui_eta(texto):
    COLA.put(('eta', texto))

PREVENCION_SUSPENSION = None

SALTO_TIEMPO = threading.Event()

_PARAR_VIGILANTE = threading.Event()

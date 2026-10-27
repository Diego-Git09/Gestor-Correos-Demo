"""Sistema: código separado del archivo original; versión de demostración."""
import time
import subprocess
from . import configuracion as _configuracion
from . import eventos as _eventos


def activar_prevision_suspension():
    pass
    try:
        if _configuracion.ES_WINDOWS:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(2147483648 | 1 | 4)
            _eventos.PREVENCION_SUSPENSION = 'windows'
            return True
        if _configuracion.ES_MAC:
            _eventos.PREVENCION_SUSPENSION = subprocess.Popen(['caffeinate', '-dims'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return _eventos.PREVENCION_SUSPENSION.poll() is None
    except Exception:
        pass
    return False

def desactivar_prevision_suspension():
    pass
    try:
        if _configuracion.ES_WINDOWS and _eventos.PREVENCION_SUSPENSION == 'windows':
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(2147483648)
        elif _eventos.PREVENCION_SUSPENSION is not None and hasattr(_eventos.PREVENCION_SUSPENSION, 'terminate'):
            try:
                _eventos.PREVENCION_SUSPENSION.terminate()
            except Exception:
                pass
    except Exception:
        pass
    _eventos.PREVENCION_SUSPENSION = None

def vigilar_saltos_de_tiempo(tolerancia=35):
    ultimo = time.time()
    while not _eventos._PARAR_VIGILANTE.wait(5):
        ahora = time.time()
        if ahora - ultimo > tolerancia:
            _eventos.SALTO_TIEMPO.set()
        ultimo = ahora

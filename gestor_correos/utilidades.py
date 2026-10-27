"""Utilidades: código separado del archivo original; versión de demostración."""
import os
import re
import time
import subprocess
from datetime import datetime, timedelta
from tkinter import ttk, messagebox, filedialog
from . import configuracion as _configuracion
from . import eventos as _eventos


def formatear_duracion(seg):
    seg = int(max(0, seg))
    h, resto = divmod(seg, 3600)
    m = resto // 60
    return f'{h} h {m:02d} min' if h else f'{max(m, 1)} min'

def texto_eta(restantes, seg_por_contacto, contador_bloque):
    lotes = (contador_bloque + restantes) // 25 - contador_bloque // 25
    seg = restantes * seg_por_contacto + lotes * _configuracion.PAUSA_LOTE_PROM
    fin = datetime.now() + timedelta(seconds=seg)
    hora = fin.strftime('%H:%M') if fin.date() == datetime.now().date() else fin.strftime('%d/%m %H:%M')
    return f'⏱ Tiempo restante estimado: {formatear_duracion(seg)}  |  Termina aprox. a las {hora}'

def dormir(segundos):
    fin = time.time() + segundos
    while time.time() < fin and (not _eventos.DETENER.is_set()):
        time.sleep(max(0.0, min(0.5, fin - time.time())))

def log_debug(contexto, error):
    """Deja constancia de un error 'tragado' sin interrumpir el flujo (queda en logs_ejecucion)."""
    texto = str(error).strip()
    primera = texto.splitlines()[0] if texto else ''
    print(f'    ⚙️ [{contexto}] {type(error).__name__}: {primera}')

def abrir_ruta(ruta):
    """Abre un archivo o carpeta con la aplicación del sistema."""
    try:
        if _configuracion.ES_WINDOWS:
            os.startfile(ruta)
        elif _configuracion.ES_MAC:
            subprocess.call(['open', ruta])
        else:
            subprocess.call(['xdg-open', ruta])
    except Exception as e:
        messagebox.showerror('No se pudo abrir', f'{ruta}\n\n{e}')

def extraer_email_de_texto(texto):
    coincidencias = re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}', texto)
    return coincidencias[0] if coincidencias else None

def sanitizar_texto(texto):
    """Devuelve un str limpio: sin nulos ni caracteres de control (conserva \\n, \\r y \\t) y sin
    caracteres malformados (surrogates sueltos). None -> ''. bytes se decodifican como UTF-8."""
    if texto is None:
        return ''
    if isinstance(texto, bytes):
        texto = texto.decode('utf-8', errors='replace')
    elif not isinstance(texto, str):
        texto = str(texto)
    texto = texto.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    return _configuracion._CONTROL_RE.sub('', texto)

def restringir_permisos(ruta):
    """En macOS/Linux deja la ruta accesible solo para el usuario: 0o700 en carpetas, 0o600 en archivos.
    (Una carpeta con 0o600 no se podría abrir, por eso las carpetas llevan además el bit de ejecución.)"""
    if _configuracion.ES_WINDOWS:
        return
    try:
        if os.path.exists(ruta):
            os.chmod(ruta, 448 if os.path.isdir(ruta) else 384)
    except Exception as e:
        log_debug('permisos', e)

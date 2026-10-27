"""Conexion: código separado del archivo original; versión de demostración."""
import time
import gc
import socket
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait, Select
try:
    from urllib3.exceptions import MaxRetryError
except Exception:

    class MaxRetryError(Exception):
        pass
from . import configuracion as _configuracion
from . import correo as _correo
from . import crm as _crm
from . import eventos as _eventos
from . import excepciones as _excepciones
from . import navegador as _navegador
from . import utilidades as _utilidades


def verificar_conexion_internet(host='8.8.8.8', puerto=53, timeout=3):
    """True si se logra abrir una conexión TCP. Prueba primero host:puerto y, si falla, unos respaldos
    (por si una red corporativa bloquea el DNS externo pero deja salir el tráfico web)."""
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    for h, p in ((host, puerto), ('1.1.1.1', 443), ('8.8.8.8', 443)):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(timeout)
            sock.connect((h, p))
            return True
        except OSError:
            continue
        finally:
            try:
                sock.close()
            except Exception:
                pass
    return False

ERRORES_RED_CANDIDATOS = (ConnectionError, MaxRetryError, TimeoutException, WebDriverException)

def es_error_de_red(error):
    """True solo si el error PUDO deberse a la red Y la prueba de conexión confirma que no hay internet.
    Así un TimeoutException común (elemento que no aparece) no provoca pausas innecesarias."""
    if isinstance(error, _excepciones.EnvioNoConfirmado):
        return False
    texto = str(error)
    firma_red = 'net::ERR_' in texto or 'ERR_INTERNET_DISCONNECTED' in texto
    if not isinstance(error, ERRORES_RED_CANDIDATOS) and (not firma_red):
        return False
    return not verificar_conexion_internet()

def esperar_reconexion(max_seg=_configuracion.RED_ESPERA_MAX, intervalo=_configuracion.RED_INTERVALO, hechos=0, total=1):
    """Pausa hasta que vuelva internet. True si se restablece; False si vence el tiempo o se pulsa Detener."""
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    print('⚠️ Conexión a internet perdida. Pausando y esperando reconexión...')
    inicio = time.time()
    while time.time() - inicio < max_seg:
        _eventos.ui_progreso(hechos, total, f'Sin internet: esperando reconexión ({int(time.time() - inicio)} s de {max_seg} s)...')
        _utilidades.dormir(intervalo)
        if _eventos.DETENER.is_set():
            return False
        transcurrido = int(time.time() - inicio)
        if verificar_conexion_internet():
            print(f'    ✓ Conexión restablecida tras {transcurrido} s.')
            return True
        print(f'    ⏳ Sin conexión ({transcurrido} s de {max_seg} s). Reintentando en {intervalo} s...')
    print(f'    ⚠️ Se agotó el tiempo de espera ({max_seg} s) sin conexión a internet.')
    return False

def reciclar_navegadores(drv_crm, drv_gmail, headless, ruta_driver, user_crm, pass_crm):
    """Cierra ambos Chrome, libera memoria, los vuelve a crear y reinicia las sesiones.
    Devuelve (drv_crm, drv_gmail, wait). El avance del bucle no se pierde."""
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    print(f'♻️ Reciclaje preventivo de memoria (cada {_configuracion.RECICLAJE_CADA} contactos): reiniciando navegadores...')
    _navegador.cerrar_driver(drv_gmail)
    _navegador.cerrar_driver(drv_crm)
    gc.collect()
    if not verificar_conexion_internet():
        esperar_reconexion()
    time.sleep(2)
    ultimo_error = None
    for intento in range(1, 3):
        nuevo_crm = nuevo_gmail = None
        try:
            nuevo_crm = _navegador.crear_driver(_configuracion.PERFIL_CRM, headless, ruta_driver, '0,0')
            nuevo_gmail = _navegador.crear_driver(_configuracion.PERFIL_GMAIL, headless, ruta_driver, '60,60')
            wait = WebDriverWait(nuevo_crm, 15)
            _crm.login_crm(nuevo_crm, user_crm, pass_crm)
            nuevo_gmail = _correo.garantizar_sesion_gmail(nuevo_gmail, headless, ruta_driver)
            if nuevo_gmail is None:
                raise RuntimeError('No se pudo verificar la sesión de Gmail tras el reciclaje.')
            gc.collect()
            print('    ✓ Navegadores reiniciados y sesiones verificadas.')
            return (nuevo_crm, nuevo_gmail, wait)
        except Exception as e:
            ultimo_error = e
            primera = str(e).splitlines()[0] if str(e) else type(e).__name__
            print(f'    ⚠️ Falló el reciclaje (intento {intento}/2): {primera}')
            _navegador.cerrar_driver(nuevo_gmail)
            _navegador.cerrar_driver(nuevo_crm)
            time.sleep(3)
    raise RuntimeError(f'No se pudieron reiniciar los navegadores: {ultimo_error}')

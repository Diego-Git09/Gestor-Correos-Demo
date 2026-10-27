"""Navegador: código separado del archivo original; versión de demostración."""
import os
import time
import threading
import subprocess
import shutil
try:
    import psutil
except ImportError:
    psutil = None
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from . import configuracion as _configuracion
from . import eventos as _eventos
from . import utilidades as _utilidades


def cerrar_sesion_gmail():
    """Elimina el perfil persistente de Gmail para solicitar un nuevo inicio de sesión."""
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    try:
        perfil = os.path.realpath(_configuracion.PERFIL_GMAIL)
        directorio_perfiles = os.path.realpath(os.path.join(_configuracion._HOME, 'GestorCorreosDemo_perfiles'))
        if os.path.dirname(perfil) != directorio_perfiles or os.path.basename(perfil) != 'gmail':
            raise ValueError('La ruta del perfil de Gmail no es segura.')
        if os.path.exists(perfil):
            shutil.rmtree(perfil)
        return True
    except Exception as error:
        print(f'No se pudo cerrar la sesión de Gmail: {error}')
        return False

def cerrar_alertas_pendientes(driver):
    for _ in range(3):
        try:
            driver.switch_to.alert.accept()
            time.sleep(0.4)
        except Exception:
            return

def app_frontal_mac():
    if not _configuracion.ES_MAC:
        return None
    try:
        out = subprocess.check_output(['osascript', '-e', 'tell application "System Events" to get name of first application process whose frontmost is true'], timeout=5)
        return out.decode().strip() or None
    except Exception:
        return None

def devolver_foco_mac(nombre_app):
    if _configuracion.ES_MAC and nombre_app:
        try:
            subprocess.call(['osascript', '-e', f'tell application "{nombre_app}" to activate'], timeout=5)
        except Exception:
            pass

def chrome_instalado():
    if _configuracion.ES_MAC:
        return any((os.path.exists(p) for p in ('/Applications/Google Chrome.app', os.path.expanduser('~/Applications/Google Chrome.app'))))
    if _configuracion.ES_WINDOWS:
        rutas = (os.path.join(os.environ.get('ProgramFiles', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'), os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'), os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'))
        return any((os.path.exists(p) for p in rutas))
    return True

def obtener_ruta_driver():
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    if _configuracion.ES_MAC:
        from webdriver_manager.chrome import ChromeDriverManager
        return ChromeDriverManager().install()
    return None

def iniciar_chrome(opciones, ruta_driver):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    if ruta_driver:
        return webdriver.Chrome(service=Service(ruta_driver), options=opciones)
    try:
        return webdriver.Chrome(options=opciones)
    except WebDriverException as e:
        texto = str(e).lower()
        if 'failed to start' in texto or 'devtoolsactiveport' in texto:
            raise
        from webdriver_manager.chrome import ChromeDriverManager
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opciones)

def limpiar_candados_perfil(perfil_dir):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    try:
        for f in os.listdir(perfil_dir):
            es_candado = f.startswith('Singleton') or (_configuracion.ES_WINDOWS and f.lower() == 'lockfile')
            if es_candado:
                try:
                    os.remove(os.path.join(perfil_dir, f))
                except OSError:
                    pass
    except OSError:
        pass

def _tamano_mb(ruta):
    total = 0
    for raiz, _, archivos in os.walk(ruta):
        for nombre in archivos:
            try:
                total += os.path.getsize(os.path.join(raiz, nombre))
            except OSError:
                pass
    return total / 1048576

def limpiar_cache_perfil(perfil_dir):
    """Si el perfil de Chrome supera UMBRAL_CACHE_MB, borra solo cachés regenerables.
    No toca cookies ni la sesión iniciada."""
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    try:
        if _tamano_mb(perfil_dir) <= _configuracion.UMBRAL_CACHE_MB:
            return
        for base in (perfil_dir, os.path.join(perfil_dir, 'Default')):
            for nombre in _configuracion.CARPETAS_CACHE:
                ruta = os.path.join(base, nombre)
                if os.path.isdir(ruta):
                    shutil.rmtree(ruta, ignore_errors=True)
        print('    ✓ Se limpió la caché del perfil de Chrome (la sesión sigue iniciada).')
    except Exception as e:
        _utilidades.log_debug('limpieza de caché', e)

def crear_driver(perfil_dir, headless, ruta_driver, posicion='0,0'):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    perfil_normalizado = os.path.normcase(os.path.abspath(perfil_dir))
    if perfil_normalizado in _eventos._PERFILES_BLOQUEADOS:
        raise RuntimeError('El Chrome anterior no cerró correctamente. Cierra el Chrome del bot y reinicia la aplicación antes de reutilizar su perfil.')
    os.makedirs(perfil_dir, exist_ok=True)
    _utilidades.restringir_permisos(_configuracion.PERFILES_DIR)
    _utilidades.restringir_permisos(perfil_dir)
    limpiar_candados_perfil(perfil_dir)
    limpiar_cache_perfil(perfil_dir)
    es_crm = os.path.normcase(os.path.abspath(perfil_dir)) == os.path.normcase(os.path.abspath(_configuracion.PERFIL_CRM))
    o = Options()
    if not _configuracion.ES_WINDOWS and (not _configuracion.ES_MAC):
        o.binary_location = '/usr/bin/google-chrome'
        o.add_argument('--ozone-platform=x11')
    o.add_argument(f'--user-data-dir={perfil_dir}')
    o.add_argument('--disable-blink-features=AutomationControlled')
    o.add_experimental_option('excludeSwitches', ['enable-automation'])
    o.add_experimental_option('useAutomationExtension', False)
    o.add_argument('--disable-notifications')
    o.add_argument('--no-first-run')
    o.add_argument('--no-default-browser-check')
    o.add_argument('--hide-crash-restore-bubble')
    o.add_argument('--remote-debugging-port=0')
    o.add_argument('--disable-background-timer-throttling')
    o.add_argument('--disable-renderer-backgrounding')
    o.add_argument('--disable-backgrounding-occluded-windows')
    o.add_argument('--disable-features=CalculateNativeWinOcclusion,Translate,MediaRouter,OptimizationHints')
    o.add_argument('--disable-background-networking')
    o.add_argument('--disable-sync')
    o.add_argument('--disable-default-apps')
    o.add_argument('--metrics-recording-only')
    o.add_argument('--mute-audio')
    o.add_argument('--disable-breakpad')
    o.add_argument('--window-size=1366,900')
    o.set_capability('unhandledPromptBehavior', 'accept')
    if es_crm:
        o.page_load_strategy = 'eager'
    o.add_argument('--disable-gpu')
    o.add_argument('--js-flags=--expose-gc')
    o.add_argument('--disk-cache-size=10000000')
    o.add_argument('--disable-extensions')
    o.add_argument('--disable-component-update')
    if es_crm:
        o.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2})
    if not _configuracion.ES_WINDOWS:
        o.add_argument('--no-sandbox')
        o.add_argument('--disable-dev-shm-usage')
    if headless:
        o.add_argument(_configuracion.HEADLESS_ARG)
    else:
        o.add_argument(f'--window-position={posicion}')
    drv = iniciar_chrome(o, ruta_driver)
    drv._bot_perfil = perfil_normalizado
    if headless:
        try:
            ua = drv.execute_script('return navigator.userAgent').replace('HeadlessChrome', 'Chrome')
            drv.execute_cdp_cmd('Network.setUserAgentOverride', {'userAgent': ua})
        except Exception as e:
            _utilidades.log_debug('CDP user-agent', e)
    try:
        drv.execute_cdp_cmd('Emulation.setFocusEmulationEnabled', {'enabled': True})
    except Exception as e:
        _utilidades.log_debug('CDP foco', e)
    if es_crm:
        try:
            drv.execute_cdp_cmd('Network.enable', {})
            drv.execute_cdp_cmd('Network.setBlockedURLs', {'urls': _configuracion.URLS_BLOQUEADAS_CRM})
        except Exception as e:
            _utilidades.log_debug('CDP bloqueo de recursos', e)
    return drv

def _procesos_del_driver(drv):
    """Captura solo el árbol del ChromeDriver propio, con identidad PID+fecha de creación."""
    if psutil is None:
        return []
    try:
        servicio = drv.service.process
        if servicio is None or servicio.poll() is not None:
            return []
        raiz = psutil.Process(servicio.pid)
        return [(p.pid, p.create_time()) for p in raiz.children(recursive=True) + [raiz]]
    except (psutil.Error, AttributeError):
        return []

def _procesos_vivos(identidades):
    vivos = []
    if psutil is None:
        return vivos
    for pid, creado in identidades:
        try:
            proceso = psutil.Process(pid)
            if proceso.create_time() == creado and proceso.is_running() and (proceso.status() != psutil.STATUS_ZOMBIE):
                vivos.append(proceso)
        except psutil.NoSuchProcess:
            continue
        except psutil.Error:
            raise RuntimeError('No se pudo verificar el cierre de un proceso del bot.')
    return vivos

def cerrar_driver(drv, timeout=10):
    """Cierre normal; respaldo solo sobre procesos capturados de este driver.
    Nunca mata Chrome por nombre ni toca el navegador personal. No reutiliza un perfil bloqueado.
    """
    if drv is None:
        return True
    perfil = getattr(drv, '_bot_perfil', None)
    identidades = _procesos_del_driver(drv)
    errores = []

    def cerrar():
        try:
            drv.quit()
        except Exception as error:
            errores.append(error)
    hilo = threading.Thread(target=cerrar, daemon=True)
    hilo.start()
    hilo.join(timeout)
    normal = not hilo.is_alive() and (not errores)
    cerrado = normal
    try:
        if identidades:
            vivos = _procesos_vivos(identidades)
            if vivos:
                print('    ⚠️ Cierre incompleto: terminando únicamente los procesos de este Chrome del bot...')
                for proceso in vivos:
                    try:
                        proceso.terminate()
                    except psutil.NoSuchProcess:
                        pass
                _, pendientes = psutil.wait_procs(vivos, timeout=3)
                for proceso in pendientes:
                    if any((proceso.pid == pid and proceso.create_time() == creado for pid, creado in identidades)):
                        try:
                            proceso.kill()
                        except psutil.NoSuchProcess:
                            pass
                psutil.wait_procs(pendientes, timeout=3)
            cerrado = not _procesos_vivos(identidades)
        elif not normal:
            cerrado = False
    except Exception as error:
        _utilidades.log_debug('cierre de Chrome', error)
        cerrado = False
    if not cerrado:
        if perfil:
            _eventos._PERFILES_BLOQUEADOS.add(perfil)
        print('    ⚠️ No se confirmó el cierre de Chrome. Su perfil no se volverá a abrir en esta ejecución. Instala psutil para habilitar el cierre de respaldo si aún no está instalado.')
    return cerrado

def esperar_interactuable(drv, xpaths, timeout=20):
    fin = time.time() + timeout
    while time.time() < fin:
        for xp in xpaths:
            try:
                for el in drv.find_elements(By.XPATH, xp):
                    if el.is_displayed() and el.is_enabled():
                        return el
            except StaleElementReferenceException:
                pass
        time.sleep(0.3)
    raise TimeoutException(f'No apareció un elemento interactuable: {xpaths[0]}')

def compose_abierto(drv):
    try:
        return any((e.is_displayed() for e in drv.find_elements(By.XPATH, _configuracion.XP_ASUNTO[0])))
    except Exception:
        return True

def esperar_cierre_compose(drv, timeout):
    fin = time.time() + timeout
    while time.time() < fin:
        if not compose_abierto(drv):
            return True
        time.sleep(0.5)
    return False

"""Crm: código separado del archivo original; versión de demostración."""
import time
from datetime import datetime, timedelta
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from . import configuracion as _configuracion
from . import contactos as _contactos
from . import eventos as _eventos
from . import navegador as _navegador
from . import persistencia as _persistencia
from . import utilidades as _utilidades
from . import validacion as _validacion


def _tabla_lista(driver):
    return driver.execute_script('return !window.jQuery || jQuery.active === 0') and driver.find_elements(By.CSS_SELECTOR, '#w0 table tbody')

def _esperar_recarga(driver, cuerpo_anterior):
    WebDriverWait(driver, 30).until(EC.staleness_of(cuerpo_anterior))
    WebDriverWait(driver, 30).until(_tabla_lista)

def sincronizar_contactos_crm(usuario, password, ejecutivo, headless=True, progreso=None):
    """Autentica, filtra y persiste solo al completar todas las páginas."""
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    progreso = progreso or (lambda texto: None)
    driver = None
    filas, ids_procesados, paginas = ([], set(), set())
    try:
        driver = _navegador.crear_driver(_configuracion.PERFIL_CRM, headless, _navegador.obtener_ruta_driver())
        progreso('Autenticando en el Manager CRM...')
        login_crm(driver, usuario, password)
        driver.get(_configuracion.CRM_CONTACTOS)
        wait = WebDriverWait(driver, 30)
        selector = wait.until(EC.visibility_of_element_located((By.XPATH, _configuracion.XPATH_DESPLEGABLE_EJECUTIVO)))
        cuerpo = driver.find_element(By.CSS_SELECTOR, '#w0 table tbody')
        seleccion = Select(selector)
        actual = seleccion.first_selected_option.text.strip()
        if actual != ejecutivo:
            seleccion.select_by_visible_text(ejecutivo)
            _esperar_recarga(driver, cuerpo)
        else:
            wait.until(_tabla_lista)
        pagina = 1
        while True:
            if _eventos.DETENER.is_set():
                raise RuntimeError('Sincronización cancelada; se conserva la base anterior.')
            selector_actual = Select(driver.find_element(By.XPATH, _configuracion.XPATH_DESPLEGABLE_EJECUTIVO))
            if selector_actual.first_selected_option.text.strip() != ejecutivo:
                raise RuntimeError('El filtro de ejecutivo cambió durante la paginación.')
            cuerpo = driver.find_element(By.CSS_SELECTOR, '#w0 table tbody')
            filas_pagina = []
            for fila in cuerpo.find_elements(By.CSS_SELECTOR, 'tr'):
                celdas = fila.find_elements(By.TAG_NAME, 'td')
                if len(celdas) < 7:
                    continue
                identificador = _validacion.normalizar_id(celdas[0].text)
                if not identificador:
                    continue
                filas_pagina.append(identificador)
                if identificador in ids_procesados:
                    continue
                ids_procesados.add(identificador)
                filas.append({'ID': identificador, 'Nombre Completo': celdas[1].text, 'Cliente': celdas[2].text, 'Correo': celdas[6].text.strip().lower()})
            activos = driver.find_elements(By.CSS_SELECTOR, '#w0 .pagination li.active')
            firma = (tuple(filas_pagina), tuple((x.text for x in activos)))
            if firma in paginas:
                raise RuntimeError('El paginador repitió una página; no se guardará una base incompleta.')
            paginas.add(firma)
            progreso(f'Sincronizando página {pagina}... ({len(filas)} contactos únicos encontrados)')
            if driver.find_elements(By.CSS_SELECTOR, '#w0 .pagination li.next.disabled'):
                break
            candidatos = driver.find_elements(By.XPATH, _configuracion.XPATH_PAGINADOR_SIGUIENTE)
            siguiente = None
            for enlace in candidatos:
                padre = enlace.find_element(By.XPATH, '..')
                clases = (padre.get_attribute('class') or '').split()
                if 'disabled' not in clases and enlace.is_displayed() and enlace.is_enabled() and enlace.get_attribute('href'):
                    siguiente = enlace
                    break
            if siguiente is None:
                break
            siguiente.click()
            _esperar_recarga(driver, cuerpo)
            pagina += 1
        contactos = _contactos.deduplicar_contactos(filas)
        _persistencia.escribir_json_atomico(_configuracion.CONTACTOS_FILE, {'ejecutivo': ejecutivo, 'sincronizado_en': datetime.now().isoformat(timespec='seconds'), 'contactos': contactos})
        return contactos
    finally:
        _navegador.cerrar_driver(driver)

def leer_correo_crm(drv, wait, id_contacto):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    drv.get(_configuracion.CRM_CONTACTO.format(id=id_contacto))
    for xp in _configuracion.XP_CORREO_FICHA:
        try:
            espera = 8 if xp is _configuracion.XP_CORREO_FICHA[0] else 1.5
            elem = WebDriverWait(drv, espera).until(EC.presence_of_element_located((By.XPATH, xp)))
            correo = _utilidades.extraer_email_de_texto(elem.text)
            if correo:
                return (correo, 'ficha')
        except Exception:
            continue
    correo = _utilidades.extraer_email_de_texto(drv.find_element(By.TAG_NAME, 'body').text)
    return (correo, 'pagina')

def registrar_gestion_crm(drv, wait, asunto_gestion):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    _navegador.cerrar_alertas_pendientes(drv)
    btn_email = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'panel') or contains(@class,'card') or contains(@class,'box') or contains(.,'Gestiones')]//a[contains(translate(., 'EMAIL', 'email'), 'email') and not(contains(@href, 'contacto'))] | //li/a[contains(.,'Email')]")))
    drv.execute_script('arguments[0].click();', btn_email)
    input_asunto = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@id='gestiones-asunto' or @name='Gestiones[asunto]' or contains(@id,'asunto')]")))
    input_asunto.clear()
    input_asunto.send_keys(asunto_gestion)
    time.sleep(0.5)
    btn_crear = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Crear') or @type='submit']")))
    drv.execute_script('arguments[0].click();', btn_crear)
    try:
        WebDriverWait(drv, 10).until(EC.invisibility_of_element(input_asunto))
        return True
    except TimeoutException:
        return False

def login_crm(drv_crm, user_crm, pass_crm):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    drv_crm.get(_configuracion.CRM_LOGIN)
    try:
        input_pass = WebDriverWait(drv_crm, 8).until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))
    except TimeoutException:
        if '/site/login' in drv_crm.current_url:
            raise RuntimeError('No se pudo verificar el formulario de ingreso del Manager.')
        print('    (sesión del Manager ya iniciada)')
        return
    input_user = drv_crm.find_element(By.XPATH, "//input[@type='password']/ancestor::form//input[@type='text' or contains(@name,'username')]")
    input_user.clear()
    input_user.send_keys(user_crm)
    input_pass.clear()
    input_pass.send_keys(pass_crm)
    btn_login = drv_crm.find_element(By.XPATH, "//button[contains(text(),'Login') or @type='submit'] | //input[@type='submit']")
    drv_crm.execute_script('arguments[0].click();', btn_login)
    try:
        WebDriverWait(drv_crm, 30).until(lambda d: '/site/login' not in d.current_url and (not any((e.is_displayed() for e in d.find_elements(By.XPATH, "//input[@type='password']")))))
    except TimeoutException as error:
        raise RuntimeError('El Manager no confirmó el ingreso. Revisa usuario y contraseña.') from error

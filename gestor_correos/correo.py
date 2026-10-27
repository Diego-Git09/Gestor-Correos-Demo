"""Correo: código separado del archivo original; versión de demostración."""
import os
import time
import random
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys
from . import configuracion as _configuracion
from . import eventos as _eventos
from . import excepciones as _excepciones
from . import navegador as _navegador
from . import utilidades as _utilidades


def resetear_gmail(drv):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    _navegador.cerrar_alertas_pendientes(drv)
    try:
        drv.get('about:blank')
    except WebDriverException:
        _navegador.cerrar_alertas_pendientes(drv)
        drv.get('about:blank')
    _navegador.cerrar_alertas_pendientes(drv)

def asegurar_sesion_gmail(drv, headless, timeout=None):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    if timeout is None:
        timeout = 40 if headless else _configuracion.ESPERA_LOGIN_GMAIL
    drv.get(_configuracion.GMAIL_INBOX)
    fin = time.time() + timeout
    login_forzado = False
    ultimo_error = None
    while time.time() < fin:
        try:
            for h in list(drv.window_handles):
                drv.switch_to.window(h)
                url = drv.current_url
                if 'mail.google.com/mail' in url and drv.find_elements(By.XPATH, _configuracion.XP_BANDEJA):
                    return True
                if not headless and (not login_forzado) and ('workspace.google.com' in url):
                    login_forzado = True
                    drv.get(_configuracion.GMAIL_LOGIN)
        except Exception as e:
            if str(e) != ultimo_error:
                ultimo_error = str(e)
                _utilidades.log_debug('sesión Gmail', e)
        time.sleep(1)
    return False

def garantizar_sesion_gmail(drv_gmail, headless, ruta_driver):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    if asegurar_sesion_gmail(drv_gmail, headless):
        return drv_gmail
    _navegador.cerrar_driver(drv_gmail)
    time.sleep(3)
    _navegador.limpiar_candados_perfil(_configuracion.PERFIL_GMAIL)
    print(f'    ⚠️ Gmail sin sesión. Se abrió una ventana: inicia sesión ahí (tienes {_configuracion.ESPERA_LOGIN_GMAIL // 60} minutos).')
    _eventos.ui_progreso(0, 1, 'Inicia sesión en Gmail en la ventana que se abrió...')
    _eventos.ui_aviso('info', 'Inicia sesión en Gmail', 'Gmail no tiene sesión iniciada.\n\nInicia sesión en la ventana de Chrome que se abrió. Cuando veas tu bandeja de entrada, el bot continúa solo.')
    drv_vis = _navegador.crear_driver(_configuracion.PERFIL_GMAIL, False, ruta_driver, '60,60')
    try:
        ok = asegurar_sesion_gmail(drv_vis, False, _configuracion.ESPERA_LOGIN_GMAIL)
        time.sleep(3)
    finally:
        _navegador.cerrar_driver(drv_vis)
        time.sleep(3)
        _navegador.limpiar_candados_perfil(_configuracion.PERFIL_GMAIL)
    if not ok:
        return None
    return _navegador.crear_driver(_configuracion.PERFIL_GMAIL, headless, ruta_driver, '60,60')

def escribir_en_cuerpo(drv, cuerpo, texto):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    try:
        drv.execute_script(_configuracion.JS_CARET_INICIO, cuerpo)
        drv.execute_script(_configuracion.JS_INSERTAR_LINEAS, cuerpo, texto.split('\n'))
    except WebDriverException:
        cuerpo.click()
        for _ in range(8):
            cuerpo.send_keys(Keys.UP)
            time.sleep(0.05)
        cuerpo.send_keys(texto)
    time.sleep(0.6)
    primera = next((l.strip() for l in texto.split('\n') if l.strip()), '')
    if primera and primera[:12] not in cuerpo.text:
        raise RuntimeError('El texto no quedó escrito en el cuerpo del correo')

def adjuntar_pdf(drv, ruta_pdf, timeout=90):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    nombre = os.path.basename(ruta_pdf).lower()
    clave = nombre[:15]
    inputs = drv.find_elements(By.XPATH, _configuracion.XP_INPUT_ARCHIVO[0]) or drv.find_elements(By.XPATH, _configuracion.XP_INPUT_ARCHIVO[1])
    if not inputs:
        raise RuntimeError('No se encontró el input de adjuntos')
    inputs[-1].send_keys(os.path.abspath(ruta_pdf))
    fin = time.time() + timeout
    estables = 0
    while time.time() < fin:
        est = drv.execute_script(_configuracion.JS_ESTADO_ADJUNTO)
        if clave in est['texto'] and est['subiendo'] == 0:
            estables += 1
            if estables >= 3:
                return
        else:
            estables = 0
        time.sleep(0.7)
    raise TimeoutException('El adjunto no terminó de subir')

def _dialogo_redaccion(drv):
    """Una única ventana visible con asunto; evita seleccionar el buscador u otro diálogo."""
    visibles = []
    for dialogo in drv.find_elements(By.XPATH, _configuracion.XP_DIALOGO):
        try:
            if dialogo.is_displayed() and any((e.is_displayed() for e in dialogo.find_elements(By.XPATH, ".//input[@name='subjectbox']"))):
                visibles.append(dialogo)
        except StaleElementReferenceException:
            continue
    if len(visibles) != 1:
        raise _excepciones.DestinatarioNoRegistrado('No hay una única ventana de redacción lista en Gmail.')
    return visibles[0]

def _campo_para(drv):
    dialogo = _dialogo_redaccion(drv)
    for xpath in _configuracion.XP_PARA:
        for campo in dialogo.find_elements(By.XPATH, '.' + xpath):
            if campo.is_displayed() and campo.is_enabled():
                return campo
    raise _excepciones.DestinatarioNoRegistrado('No apareció el campo Para dentro de la redacción.')

def _correos_destinatarios(drv):
    dialogo = _dialogo_redaccion(drv)
    correos = set()
    for chip in dialogo.find_elements(By.XPATH, './/*[@email or @data-hovercard-id]'):
        if not chip.is_displayed():
            continue
        if chip.find_elements(By.XPATH, "./ancestor::*[@contenteditable='true']"):
            continue
        valor = chip.get_attribute('email') or chip.get_attribute('data-hovercard-id') or ''
        valor = valor.strip().lower()
        if _configuracion.REGEX_EMAIL.fullmatch(valor):
            correos.add(valor)
    return correos

def destinatario_registrado(drv, correo):
    """Solo acepta el destinatario esperado como chip; texto suelto no es suficiente."""
    try:
        return _correos_destinatarios(drv) == {correo.strip().lower()}
    except (_excepciones.DestinatarioNoRegistrado, StaleElementReferenceException):
        return False

def escribir_destinatario(drv, correo):
    """Reobtiene los elementos y espera hasta 10 s por un chip, sin pausas fijas cortas."""
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    correo = correo.strip().lower()
    for intento in range(1, 4):
        try:
            para = WebDriverWait(drv, 30, poll_frequency=0.3, ignored_exceptions=(_excepciones.DestinatarioNoRegistrado, StaleElementReferenceException)).until(_campo_para)
            actuales = _correos_destinatarios(drv)
            if actuales == {correo}:
                return
            if actuales:
                raise _excepciones.DestinatarioNoRegistrado('Hay otros destinatarios en la redacción; se cancela el envío.')
            para.click()
            para.send_keys(_configuracion.TECLA_MOD, 'a')
            para.send_keys(Keys.BACKSPACE)
            para.send_keys(correo)
            para.send_keys(Keys.ENTER)
            WebDriverWait(drv, 10, poll_frequency=0.3, ignored_exceptions=(StaleElementReferenceException,)).until(lambda d: destinatario_registrado(d, correo))
            return
        except (TimeoutException, StaleElementReferenceException, _excepciones.DestinatarioNoRegistrado) as error:
            if isinstance(error, _excepciones.DestinatarioNoRegistrado) and 'otros destinatarios' in str(error):
                raise
            print(f'    ⚠️ El destinatario no se confirmó (intento {intento}/3).')
            if intento == 3:
                raise _excepciones.DestinatarioNoRegistrado(f'Gmail no registró el destinatario {correo}') from error

def componer_y_enviar(drv, correo, asunto, texto, ruta_pdf):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    resetear_gmail(drv)
    drv.get(_configuracion.GMAIL_COMPOSE)
    escribir_destinatario(drv, correo)
    _navegador.esperar_interactuable(drv, _configuracion.XP_ASUNTO, 15).send_keys(asunto)
    time.sleep(random.uniform(0.4, 0.8))
    cuerpo = _navegador.esperar_interactuable(drv, _configuracion.XP_CUERPO, 15)
    escribir_en_cuerpo(drv, cuerpo, texto)
    if ruta_pdf and os.path.exists(ruta_pdf):
        print('    📎 Adjuntando PDF y esperando a que termine de subir...')
        adjuntar_pdf(drv, ruta_pdf)
        print('    ✓ Adjunto cargado.')
    cuerpo = _navegador.esperar_interactuable(drv, _configuracion.XP_CUERPO, 10)
    if not destinatario_registrado(drv, correo):
        raise _excepciones.DestinatarioNoRegistrado('El destinatario cambió o dejó de estar confirmado antes del envío.')
    try:
        cuerpo.send_keys(_configuracion.TECLA_MOD, Keys.ENTER)
        if not _navegador.esperar_cierre_compose(drv, 10):
            try:
                btn = _navegador.esperar_interactuable(drv, _configuracion.XP_BTN_ENVIAR, 5)
                try:
                    btn.click()
                except Exception:
                    drv.execute_script('arguments[0].click();', btn)
            except TimeoutException:
                pass
            if not _navegador.esperar_cierre_compose(drv, 30):
                raise _excepciones.EnvioNoConfirmado('La ventana de redacción no se cerró: envío no confirmado')
        time.sleep(_configuracion.ESPERA_POST_ENVIO)
    except _excepciones.EnvioNoConfirmado:
        raise
    except Exception as error:
        raise _excepciones.EnvioNoConfirmado(f'No se pudo confirmar el resultado del envío: {error}') from error
    print('    ✓ Gmail cerró la redacción (correo enviado).')

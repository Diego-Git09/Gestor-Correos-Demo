"""Automatizacion: código separado del archivo original; versión de demostración."""
import os
import time
import random
import threading
import shutil
from datetime import datetime, timedelta
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait, Select
from . import conexion as _conexion
from . import configuracion as _configuracion
from . import contactos as _contactos
from . import correo as _correo
from . import crm as _crm
from . import documentos as _documentos
from . import eventos as _eventos
from . import excepciones as _excepciones
from . import navegador as _navegador
from . import plantillas as _plantillas
from . import reportes as _reportes
from . import sistema as _sistema
from . import utilidades as _utilidades
from . import validacion as _validacion


def ejecutar_bot(user_crm, pass_crm, inicio_idx, fin_idx, ruta_pdf, headless, plantilla_asunto, plantilla_cuerpo, asunto_gestion, dry_run=False, reintento_confirmado_id=None, solo_gestion_id=None, log_destino=None, solo_ids=None):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    reintento_confirmado_id = set(reintento_confirmado_id or ())
    solo_gestion_id = set(solo_gestion_id or ())
    solo_ids = set(solo_ids or ())
    _sistema.activar_prevision_suspension()
    _eventos.SALTO_TIEMPO.clear()
    _eventos._PARAR_VIGILANTE.clear()
    threading.Thread(target=_sistema.vigilar_saltos_de_tiempo, daemon=True).start()
    drv_crm = None
    drv_gmail = None
    dir_pdf_temp = None
    try:
        if not _navegador.chrome_instalado():
            _eventos.ui_aviso('error', 'Chrome no encontrado', 'Instala Google Chrome en Aplicaciones y vuelve a intentar.')
            return
        if not os.path.exists(_configuracion.CONTACTOS_FILE):
            _eventos.ui_aviso('error', 'Error', f'No se encontró el archivo:\n{_configuracion.CONTACTOS_FILE}')
            return
        df = _contactos.cargar_contactos()
        total_contactos = len(df)
        if total_contactos == 0 or inicio_idx < 1 or inicio_idx > total_contactos:
            _eventos.ui_aviso('error', 'Error de Rango', f'El contacto inicial debe estar entre 1 y {total_contactos}.')
            return
        if fin_idx > total_contactos:
            print(f'ℹ️ La base tiene {total_contactos} contactos; se ajusta el rango final de {fin_idx} a {total_contactos}.')
            fin_idx = total_contactos
        if inicio_idx > fin_idx:
            _eventos.ui_aviso('error', 'Error de Rango', 'El contacto inicial no puede ser mayor que el final.')
            return
        df_bloque = df[inicio_idx - 1:fin_idx]
        total_bloque = len(df_bloque)
        stats = {'enviados': 0, 'solo_gestion': 0, 'sin_correo': 0, 'errores': 0, 'omitidos': 0, 'pendientes': 0, 'prueba': 0, 'ya_hechos': 0}
        problemas = []

        def contar(clave):
            stats[clave] += 1
            _eventos.ui_stats(stats)

        def registrar_resultado(*args):
            if not dry_run:
                _reportes.registrar_log(*args, ruta=log_destino)
        print(f'🖥️ Sistema detectado: {_configuracion.NOMBRE_SO}')
        print(f"🚀 Iniciando automatización para {total_bloque} contactos ({('segundo plano / headless' if headless else 'ventanas visibles')})...")
        print(f'✉️ Asunto: {plantilla_asunto}')
        print(f'📝 Asunto de la gestión: {asunto_gestion}')
        if dry_run:
            print('🔎 Modo prueba activado: no se envía ni se registra gestión real.')
        if solo_ids:
            print(f'🔁 Revisión de pendientes: solo se procesarán {len(solo_ids)} contacto(s) seleccionado(s).')
        if ruta_pdf:
            print(f'📎 Adjunto cargado: {os.path.basename(ruta_pdf)}')
            ruta_pdf, dir_pdf_temp = _documentos.preparar_pdf_adjunto(ruta_pdf)
        _eventos.ui_progreso(0, total_bloque, 'Iniciando navegadores...')
        ruta_driver = _navegador.obtener_ruta_driver()
        app_previa = _navegador.app_frontal_mac()
        completados = 0
        drv_crm = _navegador.crear_driver(_configuracion.PERFIL_CRM, headless, ruta_driver, '0,0')
        drv_gmail = _navegador.crear_driver(_configuracion.PERFIL_GMAIL, headless, ruta_driver, '60,60')
        if not headless:
            _navegador.devolver_foco_mac(app_previa)
        wait = WebDriverWait(drv_crm, 15)
        _eventos.ui_progreso(0, total_bloque, 'Entrando al Manager...')
        print('-> Entrando al Manager...')
        _crm.login_crm(drv_crm, user_crm, pass_crm)
        _eventos.ui_progreso(0, total_bloque, 'Verificando sesión de Gmail...')
        print('-> Verificando sesión de Gmail...')
        drv_gmail = _correo.garantizar_sesion_gmail(drv_gmail, headless, ruta_driver)
        if drv_gmail is None:
            _eventos.ui_aviso('error', 'Gmail sin sesión', 'No se detectó el inicio de sesión de Gmail a tiempo. Vuelve a intentar.')
            return
        print('    ✓ Gmail listo.')
        correos_enviados = _reportes.cargar_correos_enviados()
        estados_log_activo = _reportes.cargar_estados_log_activo()
        contador_bloque = 0
        t_bucle = time.time()
        t_pausas = 0.0
        msg_eta = _utilidades.texto_eta(total_bloque, _configuracion.SEG_POR_CONTACTO_INICIAL, 0)
        print(msg_eta)
        _eventos.ui_eta(msg_eta)
        iterador = iter(enumerate(((inicio_idx - 1 + k, fila) for k, fila in enumerate(df_bloque)), start=1))
        reanudar = None
        reanudaciones_red = {}
        enviados_antes_del_corte = set()
        procesados = 0
        while True:
            if reanudar is not None:
                n, (index, row) = reanudar
                reanudar = None
            else:
                try:
                    n, (index, row) = next(iterador)
                except StopIteration:
                    completados = total_bloque
                    break
            completados = n - 1
            if completados >= 1:
                prom = (time.time() - t_bucle - t_pausas) / completados
                _eventos.ui_eta(_utilidades.texto_eta(total_bloque - completados, prom, contador_bloque))
            if _eventos.DETENER.is_set():
                break
            if _eventos.SALTO_TIEMPO.is_set():
                _eventos.SALTO_TIEMPO.clear()
                print('    ⚠️ El equipo estuvo congelado o en reposo. Se reinicia Gmail antes de seguir.')
                time.sleep(5)
                try:
                    _correo.resetear_gmail(drv_gmail)
                    _navegador.cerrar_alertas_pendientes(drv_crm)
                except Exception as e:
                    _utilidades.log_debug('reinicio tras reposo', e)
            posicion_real = index + 1
            id_contacto = str(row['ID']).strip()
            nombre_cliente = _validacion.obtener_nombre(row)
            correo_cliente = None
            envio_ok = False
            ya_enviado = False
            if not id_contacto:
                print(f'    ⏭️ La fila {posicion_real} de la base JSON no tiene ID; se omite.')
                contar('omitidos')
                continue
            if solo_ids and id_contacto not in solo_ids:
                continue
            estado_previo = estados_log_activo.get(id_contacto, '').upper()
            reintento_manual = id_contacto in reintento_confirmado_id or id_contacto in solo_gestion_id
            if estado_previo and (not reintento_manual):
                if estado_previo.startswith(_configuracion.ESTADOS_PENDIENTES):
                    print(f'    ⏭️ [{posicion_real}/{total_contactos}] ID {id_contacto} ({nombre_cliente}): estado previo {estado_previo}. Queda pendiente para revisión manual.')
                    contar('pendientes')
                else:
                    print(f'    ⏭️ [{posicion_real}/{total_contactos}] ID {id_contacto} ({nombre_cliente}): ya procesado ({estado_previo}).')
                    contar('ya_hechos')
                continue
            _eventos.ui_progreso(completados, total_bloque, f'Procesando {n} de {total_bloque} (fila {posicion_real}): {nombre_cliente}')
            if reanudaciones_red.get(id_contacto, 0):
                print(f'\n[{posicion_real}/{total_contactos}] Reanudando tras corte de internet: {nombre_cliente} (ID: {id_contacto})...')
            else:
                print(f'\n[{posicion_real}/{total_contactos}] Procesando: {nombre_cliente} (ID: {id_contacto})...')
            if _validacion.normalizar_correo(row.get('Correo')) is None:
                detalle_omitido = f'Omitido: Contacto ID {id_contacto} ({nombre_cliente}) - Correo interno o inválido'
                print(f'    ⏭️ {detalle_omitido}')
                registrar_resultado(id_contacto, nombre_cliente, '', 'OMITIDO', detalle_omitido)
                contar('omitidos')
                continue
            if not reanudaciones_red.get(id_contacto, 0):
                if procesados >= _configuracion.RECICLAJE_CADA:
                    _eventos.ui_progreso(completados, total_bloque, 'Reciclando navegadores (liberando memoria)...')
                    drv_crm, drv_gmail, wait = _conexion.reciclar_navegadores(drv_crm, drv_gmail, headless, ruta_driver, user_crm, pass_crm)
                    procesados = 0
                procesados += 1
            try:
                correo_base = row.get('Correo')
                correo_crm, origen_correo = _crm.leer_correo_crm(drv_crm, wait, id_contacto)
                if not correo_crm:
                    print('    ⏭️ Sin correo en el Manager. Se pasa al siguiente.')
                    registrar_resultado(id_contacto, nombre_cliente, '', 'SIN CORREO', 'No se encontró email en el Manager')
                    contar('sin_correo')
                    continue
                correo_cliente = _validacion.normalizar_correo(correo_crm)
                if correo_cliente is None:
                    detalle_omitido = f'Omitido: Contacto ID {id_contacto} ({nombre_cliente}) - Correo del Manager interno o inválido ({correo_crm})'
                    print(f'    ⏭️ {detalle_omitido}')
                    registrar_resultado(id_contacto, nombre_cliente, correo_crm, 'OMITIDO', detalle_omitido)
                    contar('omitidos')
                    continue
                correo_base_txt = str(correo_base or '').lower()
                print(f'    ✓ Correo detectado: {correo_cliente}')
                if correo_base_txt and correo_base_txt != correo_cliente.lower():
                    print(f'    ⚠️ El correo de la base JSON ({correo_base}) difiere del Manager. Se usa el del Manager.')
                if origen_correo == 'pagina' and (not correo_base_txt or correo_base_txt != correo_cliente.lower()):
                    detalle = 'Correo tomado de la página (no de la ficha); verificar a mano'
                    print(f'    ⏭️ {detalle}. Se pasa al siguiente.')
                    registrar_resultado(id_contacto, nombre_cliente, correo_cliente, 'SIN CORREO', detalle)
                    contar('sin_correo')
                    continue
                if dry_run:
                    print('    🔎 Modo prueba: no se envía correo, no se registra gestión y no se modifica el avance.')
                    contar('prueba')
                    continue
                reintento_confirmado = id_contacto in reintento_confirmado_id
                solo_gestion_forzada = id_contacto in solo_gestion_id
                salio_antes_del_corte = id_contacto in enviados_antes_del_corte
                ya_enviado = salio_antes_del_corte or solo_gestion_forzada or ((estado_previo.startswith('ENVIADO') or correo_cliente.lower() in correos_enviados) and (not reintento_confirmado))
                solo_gestion_real = ya_enviado and (not salio_antes_del_corte)
                if salio_antes_del_corte:
                    print('    ↪ El correo ya había salido antes del corte de internet. No se reenvía, solo se registra la gestión.')
                elif ya_enviado:
                    print('    ↪ El envío se omite porque el correo ya recibió el mensaje o se indicó realizar solo la gestión. Se registra únicamente la gestión en el Manager CRM.')
                else:
                    datos = {'nombre': nombre_cliente, 'cliente': _validacion.obtener_cliente(row), 'rubro': _validacion.obtener_rubro(row)}
                    asunto_final = _plantillas.renderizar_plantilla(plantilla_asunto, datos)
                    cuerpo_final = _plantillas.renderizar_plantilla(plantilla_cuerpo, datos)
                    registrar_resultado(id_contacto, nombre_cliente, correo_cliente, 'ENVIANDO', 'Envío en curso; si este es el último estado, verifica Gmail > Enviados')
                    for intento in range(1, _configuracion.MAX_REINTENTOS_GMAIL + 1):
                        try:
                            _correo.componer_y_enviar(drv_gmail, correo_cliente, asunto_final, cuerpo_final, ruta_pdf)
                            envio_ok = True
                            break
                        except _excepciones.EnvioNoConfirmado:
                            correos_enviados.add(correo_cliente.lower())
                            raise
                        except Exception as e_g:
                            if intento == _configuracion.MAX_REINTENTOS_GMAIL:
                                raise
                            print(f'    ↻ Fallo en Gmail ({str(e_g).splitlines()[0]}). Reintento {intento + 1}...')
                            if isinstance(e_g, _excepciones.DestinatarioNoRegistrado):
                                print('    ♻️ Recuperando solo Gmail antes de reintentar este contacto (aún no se envió)...')
                                if not _navegador.cerrar_driver(drv_gmail):
                                    raise RuntimeError('No se pudo cerrar Gmail para recuperarlo de forma segura.') from e_g
                                drv_gmail = _navegador.crear_driver(_configuracion.PERFIL_GMAIL, headless, ruta_driver, '60,60')
                                drv_gmail = _correo.garantizar_sesion_gmail(drv_gmail, headless, ruta_driver)
                                if drv_gmail is None:
                                    raise RuntimeError('No se pudo recuperar la sesión de Gmail.')
                            else:
                                _correo.resetear_gmail(drv_gmail)
                            _utilidades.dormir(3)
                    correos_enviados.add(correo_cliente.lower())
                confirmada = _crm.registrar_gestion_crm(drv_crm, wait, asunto_gestion)
                if confirmada:
                    print(f'    ✓ Gestión registrada para {nombre_cliente}.')
                    registrar_resultado(id_contacto, nombre_cliente, correo_cliente, 'GESTIONADO SIN ENVÍO (correo ya enviado)' if solo_gestion_real else 'ENVIADO Y GESTIONADO', 'OK')
                    contar('solo_gestion' if solo_gestion_real else 'enviados')
                else:
                    estado = 'ENVIADO - FALLÓ GESTIÓN Manager'
                    detalle = 'El Manager no confirmó visualmente la gestión; verifica si quedó registrada.'
                    print(f'    ⚠️ {estado} para {nombre_cliente}.')
                    registrar_resultado(id_contacto, nombre_cliente, correo_cliente, estado, detalle)
                    contar('errores')
                    problemas.append({'id': id_contacto, 'nombre': nombre_cliente, 'cliente': _validacion.obtener_cliente(row), 'estado': estado, 'detalle': detalle})
                if solo_gestion_real:
                    _utilidades.dormir(random.uniform(2, 4))
                    continue
                contador_bloque += 1
                if posicion_real < fin_idx and (not _eventos.DETENER.is_set()):
                    pausa = random.uniform(8, 15)
                    print(f'    ⏳ Esperando {round(pausa, 1)}s antes del siguiente contacto...')
                    _utilidades.dormir(pausa)
                if contador_bloque % 25 == 0 and posicion_real < fin_idx and (not _eventos.DETENER.is_set()):
                    descanso = random.randint(180, 300)
                    print(f'\n☕ Lote de 25 alcanzado: pausa antispam de {round(descanso / 60, 1)} min.\n')
                    hora_reanudar = (datetime.now() + timedelta(seconds=descanso)).strftime('%H:%M:%S')
                    print(f'    ℹ️ Pausa programada: se reanuda aproximadamente a las {hora_reanudar}.')
                    _eventos.ui_progreso(completados + 1, total_bloque, f'Pausa programada: continúa a las {hora_reanudar} (puedes detener)')
                    t0 = time.time()
                    _utilidades.dormir(descanso)
                    t_pausas += time.time() - t0
            except Exception as e:
                msg = str(e).split('\n')[0]
                envio_dudoso = isinstance(e, _excepciones.EnvioNoConfirmado)
                sin_red_persistente = False
                if _conexion.es_error_de_red(e):
                    if envio_ok:
                        enviados_antes_del_corte.add(id_contacto)
                    if reanudaciones_red.get(id_contacto, 0) < _configuracion.RED_MAX_REANUDACIONES:
                        reanudaciones_red[id_contacto] = reanudaciones_red.get(id_contacto, 0) + 1
                        if _conexion.esperar_reconexion(_configuracion.RED_ESPERA_MAX, _configuracion.RED_INTERVALO, completados, total_bloque):
                            try:
                                _correo.resetear_gmail(drv_gmail)
                                _navegador.cerrar_alertas_pendientes(drv_crm)
                            except Exception as err:
                                _utilidades.log_debug('reinicio tras reconexión', err)
                            print('    ↻ Se reanuda el contacto desde la navegación.')
                            reanudar = (n, (index, row))
                            continue
                        sin_red_persistente = True
                transitorio = isinstance(e, (WebDriverException, TimeoutException, ConnectionError, _excepciones.DestinatarioNoRegistrado)) and (not sin_red_persistente)
                if envio_dudoso:
                    estado = 'REVISAR (envío no confirmado)'
                    detalle = f'Envío incierto: {msg}'
                elif envio_ok or ya_enviado:
                    estado = 'ENVIADO - FALLÓ GESTIÓN Manager'
                    detalle = msg
                else:
                    estado = 'ERROR'
                    detalle = f'Recuperación automática: {msg}' if transitorio else msg
                if sin_red_persistente:
                    motivo = 'Detenido por el usuario mientras esperaba la reconexión' if _eventos.DETENER.is_set() else f'Sin internet tras esperar {_configuracion.RED_ESPERA_MAX // 60} min'
                    detalle = f'{motivo}. {detalle}'
                print(f'    ❌ {estado} ID {id_contacto}: {msg}')
                registrar_resultado(id_contacto, nombre_cliente, correo_cliente or '', estado, detalle)
                contar('errores')
                problemas.append({'id': id_contacto, 'nombre': nombre_cliente, 'cliente': _validacion.obtener_cliente(row), 'estado': estado, 'detalle': msg})
                try:
                    if transitorio:
                        for driver in (drv_gmail, drv_crm):
                            _navegador.cerrar_driver(driver)
                        drv_crm = _navegador.crear_driver(_configuracion.PERFIL_CRM, headless, ruta_driver, '0,0')
                        drv_gmail = _navegador.crear_driver(_configuracion.PERFIL_GMAIL, headless, ruta_driver, '60,60')
                        wait = WebDriverWait(drv_crm, 15)
                        _crm.login_crm(drv_crm, user_crm, pass_crm)
                        drv_gmail = _correo.garantizar_sesion_gmail(drv_gmail, headless, ruta_driver)
                        if drv_gmail is None:
                            raise RuntimeError('No se pudo recuperar la sesión de Gmail.')
                        print('    ✓ Navegadores recuperados. Se continúa con el siguiente contacto.')
                        procesados = 0
                    else:
                        _correo.resetear_gmail(drv_gmail)
                        _navegador.cerrar_alertas_pendientes(drv_crm)
                except Exception as rec:
                    print(f'    ❌ No se pudo recuperar la sesión: {rec}')
                    _eventos.COLA.put(('problemas', list(problemas)))
                    if transitorio:
                        raise
                _utilidades.dormir(random.uniform(3, 6))
                continue
        detenido = _eventos.DETENER.is_set()
        print('\n⏳ Finalizando...')
        _eventos.ui_eta('')
        time.sleep(2)
        resumen = f"✅ Correos enviados con éxito: {stats['enviados']}\n❌ Correos fallidos: {stats['errores']}\n⏭️ Contactos omitidos (correo no válido o interno): {stats['omitidos']}\n🕒 Contactos pendientes (revisión manual, no se tocaron): {stats['pendientes']}"
        if stats['ya_hechos']:
            resumen += f"\n✔ Ya procesados en ejecuciones anteriores: {stats['ya_hechos']}"
        if stats['solo_gestion']:
            resumen += f"\n↪ Solo gestión (correo repetido): {stats['solo_gestion']}"
        if stats['sin_correo']:
            resumen += f"\n📭 Sin correo en el Manager: {stats['sin_correo']}"
        if stats['prueba']:
            resumen += f"\n🔎 Contactos validados en modo prueba: {stats['prueba']}"
        if solo_ids:
            rango_txt = f'Revisión de pendientes: {len(solo_ids)} contacto(s) seleccionado(s).'
        elif completados > 0:
            ultima_fila = inicio_idx + completados - 1
            rango_txt = f'Se procesaron los contactos del {inicio_idx} al {ultima_fila}.'
        else:
            rango_txt = 'No se alcanzó a procesar ningún contacto.'
        nota_log = f'Reintento registrado en el reporte original:\n{log_destino}' if log_destino and (not dry_run) else f'Revisa el reporte:\n{_configuracion.LOG_FILE}'
        if detenido:
            print(f'\n⏹ Proceso detenido por el usuario. {rango_txt}')
            _eventos.ui_progreso(completados, total_bloque, 'Detenido')
            titulo = 'Campaña Finalizada (detenida por el usuario)'
        else:
            print(f'\n✅ Proceso terminado. {rango_txt}')
            _eventos.ui_progreso(total_bloque, total_bloque, 'Terminado')
            titulo = 'Campaña Finalizada'
            if dry_run:
                nota_log = 'Modo prueba: no se modificaron el reporte de envíos ni el avance guardado.'
            elif log_destino:
                nota_log = f'Reintento registrado en el reporte original:\n{log_destino}'
            else:
                completo, a_revisar = _reportes.log_completo(df)
                if completo:
                    nota_log += f'\nCampaña completa. {a_revisar} contactos requieren revisión.\nAl iniciar nuevamente se archivará el reporte y comenzará otro ciclo.'
        print(resumen)
        _eventos.ui_fin_campana(titulo, f'{rango_txt}\n\n{resumen}\n\n{nota_log}')
        if problemas:
            _eventos.COLA.put(('problemas', list(problemas)))
    finally:
        _eventos._PARAR_VIGILANTE.set()
        _sistema.desactivar_prevision_suspension()
        for d in (drv_crm, drv_gmail):
            _navegador.cerrar_driver(d)
        if dir_pdf_temp:
            shutil.rmtree(dir_pdf_temp, ignore_errors=True)

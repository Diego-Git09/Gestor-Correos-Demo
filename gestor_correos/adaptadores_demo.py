"""Servicios locales del formulario original; nunca leen cuentas o perfiles reales."""
import json
from pathlib import Path
import time

from . import configuracion as config
from . import demostracion as demo
from . import eventos

EJECUTIVO = 'Ejecutivo Demo'


def preparar_entorno():
    raiz = Path(config.BASE_DIR)
    raiz.mkdir(parents=True, exist_ok=True)
    ruta = Path(config.CONTACTOS_FILE)
    if not ruta.exists():
        sincronizar_contactos_crm()


def credenciales_manager_desde_entorno():
    # Valores de presentación fijos: no se consulta el entorno ni el llavero.
    return {'user': 'demo-local', 'password': 'valor-ficticio'}


def recuperar_credenciales():
    return None


def guardar_identidad(*args):
    """El formulario conserva sus controles, pero no guarda credenciales."""
    return True


def sincronizar_contactos_crm(usuario=None, password=None, ejecutivo=EJECUTIVO,
                             headless=True, progreso=None):
    contactos = demo.cargar_ejemplos()
    raiz = Path(config.BASE_DIR)
    raiz.mkdir(parents=True, exist_ok=True)
    if progreso:
        progreso('Cargando contactos ficticios incluidos en el proyecto…')
    Path(config.CONTACTOS_FILE).write_text(json.dumps(
        {'ejecutivo': EJECUTIVO, 'contactos': contactos}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return contactos


def resumen_previo(inicio, fin, solo_ids=None):
    contactos = seleccionar_contactos(inicio, fin, solo_ids)
    resultados = demo.preparar_demostracion(contactos)
    datos = demo.resumen(resultados)
    return (f"Contactos ficticios: {datos['total']}\n"
            f"A simular: {datos['simulados']}\n"
            f"Sin correo: {datos['omitidos']}\n\n"
            'No se abrirá Gmail ni el CRM. No se enviarán correos.')


def seleccionar_contactos(inicio, fin, solo_ids=None):
    from .contactos import cargar_contactos
    contactos = cargar_contactos()
    if not 1 <= inicio <= fin <= len(contactos):
        raise ValueError(f'Elige un rango entre 1 y {len(contactos)}, con inicio menor o igual al final.')
    seleccion = contactos[inicio - 1:fin]
    if solo_ids:
        seleccion = [c for c in seleccion if c['ID'] in solo_ids]
    return seleccion


def ejecutar_campana(user_crm, pass_crm, inicio_idx, fin_idx, ruta_pdf, headless,
                    plantilla_asunto, plantilla_cuerpo, asunto_gestion,
                    dry_run=True, reintento_confirmado_id=None, solo_gestion_id=None,
                    log_destino=None, solo_ids=None):
    """Adapta la firma anterior a la simulación. dry_run=False tampoco habilita envíos."""
    contactos = seleccionar_contactos(inicio_idx, fin_idx, solo_ids)
    resultados = demo.preparar_demostracion(contactos, plantilla_asunto, plantilla_cuerpo, ruta_pdf or None)
    procesados = []
    stats = {'enviados': 0, 'errores': 0, 'omitidos': 0, 'pendientes': 0, 'sin_correo': 0}
    eventos.COLA.put(('log', 'DEMO LOCAL · Sin cuentas, navegadores ni envíos reales.'))
    for resultado in resultados:
        if eventos.DETENER.is_set():
            eventos.COLA.put(('log', 'Simulación detenida por el usuario.'))
            break
        procesados.append(resultado)
        if resultado.estado == 'SIMULADO':
            stats['enviados'] += 1  # La ficha de la ventana está rotulada «Simulados».
        else:
            stats['omitidos'] += 1
            stats['sin_correo'] += 1
        eventos.ui_stats(stats)
        eventos.ui_progreso(len(procesados), len(resultados),
                            f'Simulación: {len(procesados)} de {len(resultados)} · 0 envíos reales')
        eventos.COLA.put(('log', f'{resultado.cliente}: {resultado.estado}'))
        eventos.DETENER.wait(.12)
    carpeta = Path(config.BASE_DIR) / 'reportes_demo'
    carpeta.mkdir(parents=True, exist_ok=True)
    reporte = carpeta / f'campana_{time.time_ns()}.json'
    demo.exportar_reporte(reporte, procesados)
    datos = demo.resumen(procesados)
    eventos.COLA.put(('log', f"Resultado: {datos['simulados']} simulados, {datos['omitidos']} omitidos, 0 envíos reales."))
    eventos.COLA.put(('eta', 'Simulación local · Sin envíos reales'))
    return procesados, reporte

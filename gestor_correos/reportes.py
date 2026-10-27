"""Reportes: código separado del archivo original; versión de demostración."""
import os
import hashlib
import time
import csv
from datetime import datetime, timedelta
from . import configuracion as _configuracion
from . import contactos as _contactos
from . import utilidades as _utilidades
from . import validacion as _validacion


def _escribir_filas_log(ruta, filas):
    existe = os.path.exists(ruta)
    with open(ruta, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';')
        if not existe:
            writer.writerow(_configuracion.ENCABEZADO_LOG)
        writer.writerows(filas)

def _unir_pendiente(ruta_log):
    """Si quedaron filas guardadas aparte (el CSV estaba abierto en Excel), las une al reporte."""
    pendiente = ruta_log + '.pendiente'
    if not os.path.exists(pendiente):
        return
    with open(pendiente, newline='', encoding='utf-8-sig') as f:
        filas = list(csv.reader(f, delimiter=';'))
    if filas:
        _escribir_filas_log(ruta_log, filas)
    os.remove(pendiente)

def registrar_log(id_contacto, nombre, correo, estado, detalle='', ruta=None):
    ruta_log = ruta or _configuracion.LOG_FILE
    fila = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id_contacto, nombre, correo if correo else 'N/A', estado, detalle]
    for _ in range(4):
        try:
            _unir_pendiente(ruta_log)
            _escribir_filas_log(ruta_log, [fila])
            return
        except PermissionError:
            time.sleep(1.5)
    with open(ruta_log + '.pendiente', mode='a', newline='', encoding='utf-8') as f:
        csv.writer(f, delimiter=';').writerow(fila)
    print(f'    ⚠️ El reporte está abierto en Excel: el registro quedó en {os.path.basename(ruta_log)}.pendiente y se unirá solo cuando lo cierres.')

def leer_log(ruta=None):
    """Filas del reporte (sin encabezado), con 6 columnas, incluyendo las del archivo .pendiente."""
    ruta = ruta or _configuracion.LOG_FILE
    filas = []
    for archivo in (ruta, ruta + '.pendiente'):
        if not os.path.exists(archivo):
            continue
        with open(archivo, newline='', encoding='utf-8-sig') as f:
            for fila in csv.reader(f, delimiter=';'):
                if len(fila) >= 5 and fila[0] != _configuracion.ENCABEZADO_LOG[0]:
                    filas.append(fila + [''] * (6 - len(fila)))
    return filas

def ultimos_estados_log(ruta=None):
    """{id: último estado} según el reporte."""
    return {fila[1].strip(): fila[4].strip() for fila in leer_log(ruta)}

def cargar_correos_enviados():
    """Correos que ya recibieron (o pudieron haber recibido) el mensaje.
    Un ENVIANDO cuenta solo si es el último estado de ese ID (si después hubo ERROR, no se envió)."""
    enviados, en_curso = (set(), {})
    for fila in leer_log():
        id_c, correo, estado = (fila[1].strip(), fila[3].strip().lower(), fila[4].strip().upper())
        if estado.startswith(('ENVIADO', 'REVISAR')):
            enviados.add(correo)
            en_curso.pop(id_c, None)
        elif estado == 'ENVIANDO':
            en_curso[id_c] = correo
        else:
            en_curso.pop(id_c, None)
    enviados.update(en_curso.values())
    return {c for c in enviados if c and c != 'n/a'}

def cargar_estados_log_activo():
    return ultimos_estados_log()

def log_completo(df):
    if not os.path.exists(_configuracion.LOG_FILE) and (not os.path.exists(_configuracion.LOG_FILE + '.pendiente')):
        return (False, 0)
    ids_base = {_validacion.normalizar_id(c['ID']) for c in df} - {''}
    if not ids_base:
        return (False, 0)
    ultimo = ultimos_estados_log()
    completo = all((i in ultimo for i in ids_base))
    a_revisar = sum((1 for i in ids_base if ultimo.get(i, '').upper().startswith(_configuracion.ESTADOS_PENDIENTES)))
    return (completo, a_revisar)

def archivar_log():
    _unir_pendiente(_configuracion.LOG_FILE)
    marca = datetime.now().strftime('%Y%m%d_%H%M')
    destino = os.path.join(_configuracion.BASE_DIR, f'reporte_envios_log_FIN_{marca}.csv')
    numero = 1
    while os.path.exists(destino):
        destino = os.path.join(_configuracion.BASE_DIR, f'reporte_envios_log_FIN_{marca}_{numero}.csv')
        numero += 1
    os.replace(_configuracion.LOG_FILE, destino)
    _escribir_filas_log(_configuracion.LOG_FILE, [])
    return destino

def cargar_contactos_pendientes_revision():
    if not os.path.exists(_configuracion.CONTACTOS_FILE):
        return []
    df = _contactos.cargar_contactos()
    posiciones = {_validacion.normalizar_id(c['ID']): fila for fila, c in enumerate(df, start=1)}
    pendientes = []
    for ruta in rutas_reportes_envios():
        ultimos = {}
        for fila in leer_log(ruta):
            id_contacto = fila[1].strip()
            if id_contacto in posiciones:
                ultimos[id_contacto] = {'fila': posiciones[id_contacto], 'id': id_contacto, 'nombre': fila[2].strip(), 'correo': '' if fila[3].strip().upper() == 'N/A' else fila[3].strip(), 'estado': fila[4].strip(), 'detalle': fila[5].strip(), 'campana': 'Campaña activa' if ruta == _configuracion.LOG_FILE else os.path.basename(ruta), 'ruta': ruta}
        pendientes.extend((item for item in ultimos.values() if item['estado'].upper().startswith(_configuracion.ESTADOS_PENDIENTES)))
    return sorted(pendientes, key=lambda item: (item['fila'], item['campana']))

def huella_plantilla(asunto, cuerpo):
    contenido = f'{asunto}\x00{cuerpo}'.encode('utf-8')
    return hashlib.sha256(contenido).hexdigest()

def rutas_reportes_envios():
    nombres = sorted((nombre for nombre in os.listdir(_configuracion.BASE_DIR) if nombre.startswith('reporte_envios_log_') and nombre.endswith('.csv')))
    rutas = [os.path.join(_configuracion.BASE_DIR, nombre) for nombre in nombres]
    if os.path.exists(_configuracion.LOG_FILE):
        rutas.append(_configuracion.LOG_FILE)
    return rutas

def preparar_campana(df):
    """Solo rota una base no vacía al iniciar explícitamente otra ejecución."""
    completo, _ = log_completo(df)
    if completo:
        archivar_log()
        return True
    if not os.path.exists(_configuracion.LOG_FILE):
        _escribir_filas_log(_configuracion.LOG_FILE, [])
    return False

def sugerir_rango(tam_lote=None):
    """Según el reporte de envíos, propone el siguiente tramo de contactos sin estado registrado.
    Devuelve None si no hay base/avance que usar; si no, un dict con inicio, fin, total y hechos
    (inicio=None cuando todos los contactos de la base JSON ya tienen estado)."""
    try:
        if not os.path.exists(_configuracion.CONTACTOS_FILE) or not os.path.exists(_configuracion.LOG_FILE):
            return None
        df = _contactos.cargar_contactos()
        total = len(df)
        if total == 0:
            return None
        con_estado = {fila[1].strip() for fila in leer_log() if fila[4].strip().upper() != 'DRY RUN'}
        ids = [_validacion.normalizar_id(c['ID']) for c in df]
        pendientes = [pos for pos, v in enumerate(ids, start=1) if v not in con_estado]
        hechos = total - len(pendientes)
        if hechos == 0:
            return None
        if not pendientes:
            return {'inicio': None, 'fin': None, 'total': total, 'hechos': hechos}
        try:
            tam = max(1, int(tam_lote))
        except (TypeError, ValueError):
            tam = _configuracion.TAM_LOTE_DEFECTO
        inicio = pendientes[0]
        return {'inicio': inicio, 'fin': min(inicio + tam - 1, total), 'total': total, 'hechos': hechos}
    except Exception:
        return None

def resumen_previo(inicio, fin, solo_ids=None):
    """Texto con lo que va a hacer el bot, para confirmar antes de iniciar (valores aproximados)."""
    df = _contactos.cargar_contactos()
    fin = min(fin, len(df))
    bloque = df[max(inicio, 1) - 1:fin]
    if solo_ids:
        bloque = [c for c in bloque if str(c['ID']).strip() in solo_ids]
    ultimos = ultimos_estados_log()
    sin_correo = sum((1 for c in bloque if _validacion.normalizar_correo(c['Correo']) is None))
    if solo_ids:
        pendientes = 0
    else:
        pendientes = sum((1 for i in (c['ID'] for c in bloque) if ultimos.get(str(i).strip(), '').upper().startswith(_configuracion.ESTADOS_PENDIENTES)))
    a_enviar = max(0, len(bloque) - sin_correo - pendientes)
    eta = _utilidades.texto_eta(a_enviar, _configuracion.SEG_POR_CONTACTO_INICIAL, 0)
    return f'Contactos en el rango: {len(bloque)}\nSin correo válido (se omiten): {sin_correo}\nPendientes de revisión (no se tocan): {pendientes}\nA procesar aprox.: {a_enviar}\n\n{eta}'

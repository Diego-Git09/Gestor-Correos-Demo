"""Persistencia: código separado del archivo original; versión de demostración."""
import os
import json
import tempfile
from . import configuracion as _configuracion
from . import reportes as _reportes
from . import utilidades as _utilidades


def cargar_config():
    try:
        with open(_configuracion.CONFIG_FILE, encoding='utf-8') as f:
            datos = json.load(f)
        if not isinstance(datos, dict):
            return {}
        datos.setdefault('dry_run', False)
        datos.setdefault('ruta_pdf', '')
        return datos
    except Exception:
        return {'dry_run': False, 'ruta_pdf': ''}

def guardar_config(asunto=None, cuerpo=None, asunto_gestion=None, tam_lote=None, dry_run=None, ruta_pdf=None, huella_campana=None):
    try:
        datos = cargar_config()
        config_anterior = dict(datos)
        if asunto is not None:
            datos['asunto'] = _utilidades.sanitizar_texto(asunto)
        if cuerpo is not None:
            datos['cuerpo'] = _utilidades.sanitizar_texto(cuerpo)
        if asunto_gestion is not None:
            datos['asunto_gestion'] = _utilidades.sanitizar_texto(asunto_gestion)
        if huella_campana is None:
            huella_campana = config_anterior.get('huella_campana') or _reportes.huella_plantilla(config_anterior.get('asunto') or _configuracion.ASUNTO_CORREO_DEFECTO, config_anterior.get('cuerpo') or _configuracion.CUERPO_CORREO_DEFECTO)
        datos['huella_campana'] = huella_campana
        if tam_lote is not None:
            datos['tam_lote'] = int(tam_lote)
        if dry_run is not None:
            datos['dry_run'] = bool(dry_run)
        if ruta_pdf is not None:
            datos['ruta_pdf'] = _utilidades.sanitizar_texto(ruta_pdf)
        actualizar_config(datos)
    except Exception as error:
        print(f'No se pudo guardar la configuración: {error}')

def escribir_json_atomico(ruta, datos):
    """Escribe completo antes de reemplazar; un fallo no destruye la base anterior."""
    fd, temporal = tempfile.mkstemp(prefix='.gestor_demo_', dir=os.path.dirname(ruta))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
            archivo.flush()
            os.fsync(archivo.fileno())
        _utilidades.restringir_permisos(temporal)
        os.replace(temporal, ruta)
    finally:
        if os.path.exists(temporal):
            os.remove(temporal)

def actualizar_config(cambios):
    with _configuracion.CONFIG_LOCK:
        datos = cargar_config()
        datos.update(cambios)
        datos.pop('ruta_excel', None)
        escribir_json_atomico(_configuracion.CONFIG_FILE, datos)

"""Contactos: código separado del archivo original; versión de demostración."""
import json
from . import configuracion as _configuracion
from . import utilidades as _utilidades
from . import validacion as _validacion


def deduplicar_contactos(filas):
    ids, contactos = (set(), [])
    for fila in filas:
        if not isinstance(fila, dict):
            raise ValueError('Registro de contacto inválido.')
        identificador = _validacion.normalizar_id(fila.get('ID'))
        if not identificador or identificador in ids:
            continue
        ids.add(identificador)
        contactos.append({'ID': identificador, 'Nombre': _validacion.primer_nombre(fila.get('Nombre Completo', fila.get('Nombre', ''))), 'Cliente': _utilidades.sanitizar_texto(str(fila.get('Cliente') or '')), 'Correo': str(fila.get('Correo') or '').strip().lower()})
    return contactos

def cargar_contactos():
    with open(_configuracion.CONTACTOS_FILE, encoding='utf-8') as archivo:
        datos = json.load(archivo)
    filas = datos.get('contactos') if isinstance(datos, dict) else datos
    if not isinstance(filas, list):
        raise ValueError('La base JSON debe contener una lista de contactos.')
    return deduplicar_contactos(filas)

def validar_cartera(ejecutivo):
    with open(_configuracion.CONTACTOS_FILE, encoding='utf-8') as archivo:
        datos = json.load(archivo)
    if not isinstance(datos, dict) or not datos.get('ejecutivo'):
        raise ValueError('Sincroniza la cartera para identificar su ejecutivo.')
    if datos['ejecutivo'].strip().casefold() != ejecutivo.strip().casefold():
        raise ValueError('La base corresponde a otro ejecutivo. Sincroniza tu cartera actual antes de iniciar.')
    if not cargar_contactos():
        raise ValueError('La cartera está vacía. Sincroniza una cartera con contactos.')

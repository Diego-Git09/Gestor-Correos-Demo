"""Validacion: código separado del archivo original; versión de demostración."""
import re
import unicodedata
from . import configuracion as _configuracion
from . import utilidades as _utilidades


def _es_nulo(valor):
    """True para None o NaN (float)."""
    return valor is None or (isinstance(valor, float) and valor != valor)

def normalizar_id(valor):
    """'123', 123 y 123.0 -> '123'. Vacío o NaN -> ''."""
    if _es_nulo(valor):
        return ''
    texto = str(valor).strip()
    if re.fullmatch('\\d+\\.0+', texto):
        texto = texto.split('.')[0]
    return '' if texto.lower() == 'nan' else texto

def normalizar_correo(valor):
    """Devuelve el correo en minúsculas si es válido y externo; si no, None."""
    if _es_nulo(valor):
        return None
    texto = str(valor).strip().lower()
    if not texto or texto == 'nan':
        return None
    if any((d in texto for d in _configuracion.DOMINIOS_INTERNOS)):
        return None
    if not _configuracion.REGEX_EMAIL.match(texto):
        return None
    local, dominio = texto.rsplit('@', 1)
    if re.fullmatch('x+', local) or re.fullmatch('(?:x+\\.)*x+', dominio):
        return None
    return texto

def _sin_acentos(texto):
    texto = texto.replace('ñ', '\x00').replace('Ñ', '\x01')
    base = ''.join((c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn'))
    return base.replace('\x00', 'ñ').replace('\x01', 'Ñ')

def _clave(palabra):
    return _sin_acentos(palabra).lower().strip(' .,;:')

def _es_titulo(palabra):
    return _clave(palabra) in _configuracion.TITULOS_NOMBRE

def _es_institucional(palabra):
    return _clave(palabra).startswith(_configuracion.PALABRAS_INSTITUCIONALES)

def _letras(palabra):
    return sum((c.isalpha() for c in palabra))

def primer_nombre(valor):
    if _es_nulo(valor):
        return _configuracion.SALUDO_GENERICO
    if str(valor).strip() == _configuracion.SALUDO_GENERICO:
        return _configuracion.SALUDO_GENERICO
    palabras = _utilidades.sanitizar_texto(str(valor)).strip().split()
    if not palabras:
        return _configuracion.SALUDO_GENERICO
    primera = palabras[0].strip('.,;:')
    genericos = {'area', 'ejecutivo', 'compras', 'contacto', 'ventas', 'admin', 'cliente'}
    if _clave(primera) in genericos or _letras(primera) < 2 or primera.lower() == 'nan':
        return _configuracion.SALUDO_GENERICO
    return primera.title()

def obtener_nombre(row):
    return row.get('Nombre') or primer_nombre(row.get('Nombre Completo', ''))

def obtener_cliente(row):
    return str(row.get('Cliente', '')).strip()

def obtener_rubro(row):
    return str(row.get('Rubro Cliente', row.get('Rubro', ''))).strip()

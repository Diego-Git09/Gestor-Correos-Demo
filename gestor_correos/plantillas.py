"""Plantillas: código separado del archivo original; versión de demostración."""
import re
from . import configuracion as _configuracion


def renderizar_plantilla(plantilla, datos):
    if not plantilla:
        return ''
    mapa = {str(k).lower(): str(v) for k, v in datos.items()}

    def reemplazo(match):
        clave = match.group(1)
        return mapa.get(clave.lower(), match.group(0))
    return re.sub('\\{([^{}]+)\\}', reemplazo, plantilla)

def variables_desconocidas(*textos):
    usadas = {m.lower() for m in re.findall('\\{(\\w+)\\}', ' '.join(textos))}
    validas = {v.lower() for v in _configuracion.VARIABLES_PLANTILLA}
    return sorted(usadas - validas)

"""Campañas locales con contactos ficticios: no abre navegadores ni envía mensajes."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .contactos import deduplicar_contactos
from .plantillas import renderizar_plantilla, variables_desconocidas
from .validacion import normalizar_correo

EJEMPLOS = Path(__file__).resolve().parent.parent / 'ejemplos' / 'contactos_demo.json'
ASUNTO = 'Presentación de productos para {cliente}'
CUERPO = 'Hola {nombre}:\n\nEste es un mensaje de demostración para {cliente}.\nNo se enviará ningún correo.\n\nSaludos,\nEquipo Demo'


@dataclass(frozen=True)
class ResultadoDemo:
    id_contacto: str
    cliente: str
    correo: str
    asunto: str
    cuerpo: str
    estado: str
    adjunto: str = ''


def cargar_ejemplos():
    """Solo utiliza el archivo ficticio incluido, nunca la configuración del original."""
    return deduplicar_contactos(json.loads(EJEMPLOS.read_text(encoding='utf-8')))


def comprobar_pdf(ruta):
    """Comprueba un PDF seleccionado sin modificarlo ni comprimirlo."""
    from pypdf import PdfReader
    archivo = Path(ruta)
    if archivo.suffix.lower() != '.pdf' or not archivo.is_file():
        raise ValueError('Selecciona un archivo PDF existente.')
    if archivo.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('La demostración admite PDF de hasta 20 MiB.')
    with archivo.open('rb') as stream:
        if stream.read(5) != b'%PDF-':
            raise ValueError('El archivo no tiene una cabecera PDF válida.')
        stream.seek(0)
        lector = PdfReader(stream)
        if lector.is_encrypted:
            raise ValueError('La demostración no abre PDF cifrados.')
        paginas = len(lector.pages)
    if paginas < 1:
        raise ValueError('El PDF debe contener al menos una página.')
    return {'nombre': archivo.name, 'paginas': paginas, 'bytes': archivo.stat().st_size}


def preparar_demostracion(contactos, asunto=ASUNTO, cuerpo=CUERPO, pdf=None):
    """Valida el lote completo antes de producir resultados; no realiza envíos."""
    if not asunto.strip() or not cuerpo.strip():
        raise ValueError('El asunto y el mensaje no pueden estar vacíos.')
    desconocidas = variables_desconocidas(asunto, cuerpo)
    if desconocidas:
        raise ValueError('Variables desconocidas: ' + ', '.join(desconocidas))
    adjunto = comprobar_pdf(pdf)['nombre'] if pdf else ''
    resultados = []
    for fila in contactos:
        correo = str(fila.get('Correo') or '').strip().lower()
        if correo and not correo.endswith('@example.invalid'):
            raise ValueError('Usa únicamente direcciones ficticias del dominio example.invalid.')
        datos = {'nombre': fila.get('Nombre', ''), 'cliente': fila.get('Cliente', ''), 'rubro': fila.get('Rubro', 'demostración')}
        resultados.append(ResultadoDemo(
            id_contacto=str(fila.get('ID', '')), cliente=datos['cliente'], correo=correo,
            asunto=renderizar_plantilla(asunto, datos), cuerpo=renderizar_plantilla(cuerpo, datos),
            estado='SIMULADO' if normalizar_correo(correo) else 'OMITIDO_SIN_CORREO', adjunto=adjunto,
        ))
    if not resultados:
        raise ValueError('Selecciona al menos un contacto.')
    return resultados


def resumen(resultados):
    return {'total': len(resultados), 'simulados': sum(r.estado == 'SIMULADO' for r in resultados),
            'omitidos': sum(r.estado != 'SIMULADO' for r in resultados), 'envios_reales': 0}


def exportar_reporte(ruta, resultados):
    """Exportación explícita con nombre elegido por el usuario; nunca sobrescribe."""
    destino = Path(ruta)
    with destino.open('x', encoding='utf-8') as stream:
        json.dump({'modo': 'demostracion', 'resumen': resumen(resultados),
                   'resultados': [asdict(r) for r in resultados]}, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


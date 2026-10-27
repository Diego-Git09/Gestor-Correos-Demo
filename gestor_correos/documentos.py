"""Documentos: código separado del archivo original; versión de demostración."""
import os
import shutil
import tempfile
from . import configuracion as _configuracion


def _comprimir_con_fitz(origen, destino):
    import fitz
    doc = fitz.open(origen)
    try:
        if hasattr(doc, 'rewrite_images'):
            try:
                doc.rewrite_images(dpi_threshold=150, dpi_target=110, quality=70)
            except Exception:
                pass
        doc.save(destino, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True, clean=True)
    finally:
        doc.close()

def _comprimir_con_pypdf(origen, destino):
    from pypdf import PdfReader, PdfWriter
    lector = PdfReader(origen)
    escritor = PdfWriter()
    for pagina in lector.pages:
        escritor.add_page(pagina)
    for pagina in escritor.pages:
        try:
            pagina.compress_content_streams()
        except Exception:
            pass
        try:
            for img in pagina.images:
                try:
                    img.replace(img.image, quality=70)
                except Exception:
                    pass
        except Exception:
            pass
    try:
        try:
            escritor.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
        except TypeError:
            escritor.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    except Exception:
        pass
    with open(destino, 'wb') as f:
        escritor.write(f)

def validar_integridad_pdf(ruta_pdf):
    if not ruta_pdf or not os.path.isfile(ruta_pdf):
        return False
    try:
        if os.path.getsize(ruta_pdf) <= 0:
            return False
    except OSError:
        return False
    try:
        import fitz
        docs = fitz.open(ruta_pdf)
        try:
            if docs.page_count <= 0:
                return False
            docs.load_page(0)
            return True
        finally:
            docs.close()
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        lector = PdfReader(ruta_pdf)
        if len(lector.pages) <= 0:
            return False
        lector.pages[0]
        return True
    except Exception:
        return False

def preparar_pdf_adjunto(ruta_pdf):
    """Devuelve (ruta_a_usar, carpeta_temporal_o_None).
    Si el PDF pesa más de UMBRAL_PDF_MB crea una copia comprimida (con el MISMO nombre de archivo,
    porque la verificación del adjunto en Gmail se basa en el nombre). Ante cualquier fallo, o si la
    copia no resulta más liviana, se usa el original."""
    if not ruta_pdf or not os.path.isfile(ruta_pdf):
        return (ruta_pdf, None)
    if not validar_integridad_pdf(ruta_pdf):
        print('   ⚠️ El PDF original no es legible; se usará sin compresión.')
        return (ruta_pdf, None)
    try:
        peso_original = os.path.getsize(ruta_pdf)
        if peso_original <= _configuracion.UMBRAL_PDF_MB * 1024 * 1024:
            return (ruta_pdf, None)
    except OSError:
        return (ruta_pdf, None)
    print(f'🗜️ El PDF pesa {peso_original / 1048576:.2f} MB (> {_configuracion.UMBRAL_PDF_MB:.1f} MB). Optimizando una copia...')
    carpeta = None
    try:
        carpeta = tempfile.mkdtemp(prefix='gestor_demo_pdf_')
        destino = os.path.join(carpeta, os.path.basename(ruta_pdf))
        comprimido = False
        for metodo in (_comprimir_con_fitz, _comprimir_con_pypdf):
            try:
                if os.path.exists(destino):
                    os.remove(destino)
                metodo(ruta_pdf, destino)
                if os.path.isfile(destino) and 0 < os.path.getsize(destino) < peso_original and validar_integridad_pdf(destino):
                    comprimido = True
                    break
            except ImportError:
                continue
            except Exception:
                continue
        if comprimido:
            print(f'   ✓ PDF optimizado: {peso_original / 1048576:.2f} MB -> {os.path.getsize(destino) / 1048576:.2f} MB')
            return (destino, carpeta)
        print('   ⚠️ La copia comprimida no pasó la validación de integridad; se usará el original.')
    except Exception:
        print('   ⚠️ Falló la compresión del PDF; se usará el original.')
    if carpeta:
        shutil.rmtree(carpeta, ignore_errors=True)
    return (ruta_pdf, None)

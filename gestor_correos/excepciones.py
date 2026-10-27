"""Excepciones: código separado del archivo original; versión de demostración."""



class DestinatarioNoRegistrado(RuntimeError):
    """Fallo anterior al envío: permite recuperar Gmail sin reenviar un correo incierto."""

class EnvioNoConfirmado(Exception):
    """Se disparó el envío pero Gmail no confirmó. NO se reintenta (evita duplicados)."""

"""Credenciales: código separado del archivo original; versión de demostración."""
import os
import hashlib
import keyring
from cryptography.fernet import Fernet
from . import configuracion as _configuracion
from . import persistencia as _persistencia


def _cifrador(crear=False):
    """La clave Fernet vive en el llavero del SO, nunca junto al token JSON."""
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    cuenta = hashlib.sha256(os.path.abspath(_configuracion.BASE_DIR).encode()).hexdigest()
    clave = keyring.get_password('GestorCorreosDemo.Fernet', cuenta)
    if clave is None:
        if not crear:
            raise ValueError('No existe la clave en el llavero del sistema.')
        clave = Fernet.generate_key().decode('ascii')
        keyring.set_password('GestorCorreosDemo.Fernet', cuenta, clave)
    return Fernet(clave.encode('ascii'))

def guardar_identidad(usuario, password, recordar, ejecutivo):
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    cambios = {'nombre_ejecutivo': ejecutivo, 'recordar_credenciales': bool(recordar), 'usuario_crm': usuario if recordar else '', 'password_cifrado': ''}
    if recordar and password:
        cambios['password_cifrado'] = _cifrador(crear=True).encrypt(password.encode('utf-8')).decode('ascii')
    _persistencia.actualizar_config(cambios)

def recuperar_credenciales():
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    datos = _persistencia.cargar_config()
    if not datos.get('recordar_credenciales') or not datos.get('password_cifrado'):
        return None
    return {'user': datos.get('usuario_crm', ''), 'password': _cifrador().decrypt(datos['password_cifrado'].encode('ascii')).decode('utf-8')}

def credenciales_manager_desde_entorno():
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    return {'user': os.getenv('BOT_CRM_USER', '').strip(), 'password': os.getenv('BOT_CRM_PASSWORD', '').strip()}

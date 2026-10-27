"""Configuracion: código separado del archivo original; versión de demostración."""
import os
import re
import sys
import threading
from pathlib import Path
import platform

VERSION = '0.1.0-demo'
ES_MAC = sys.platform == 'darwin'
SISTEMA = platform.system()
ES_WINDOWS = SISTEMA == 'Windows'
NOMBRE_SO = SISTEMA
BASE_DIR = str(Path(os.environ.get('GESTOR_DATOS_DIR', str(Path(__file__).resolve().parent.parent / 'datos'))).expanduser().resolve())
DIRECTORIO_BASE = BASE_DIR
_HOME = BASE_DIR
PERFILES_DIR = str(Path(BASE_DIR) / 'perfiles_demo')
PERFIL_GMAIL = str(Path(PERFILES_DIR) / 'correo_demo')
PERFIL_CRM = str(Path(PERFILES_DIR) / 'crm_demo')
LOGO_FILE = str(Path(__file__).resolve().parent.parent / 'recursos' / 'logo_demo.png')

TECLA_MOD = '\ue03d' if ES_MAC else '\ue009'

def ruta_recurso(nombre):
    """Ruta de un recurso empaquetado (solo lectura). Con PyInstaller vive en sys._MEIPASS."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)

LOG_FILE = os.path.join(BASE_DIR, 'reporte_envios_log.csv')

CONFIG_FILE = os.path.join(BASE_DIR, 'bot_config.json')

CONTACTOS_FILE = os.path.join(BASE_DIR, 'contactos_sincronizados.json')

CONFIG_LOCK = threading.RLock()

LOGO_MAX_ANCHO = 360

LOGO_MAX_ALTO = 70

ASUNTO_GESTION = 'Catálogo de demostración'

ASUNTO_CORREO_DEFECTO = 'Consulta sobre necesidad de productos'

CUERPO_CORREO_DEFECTO = 'Hola {nombre}, espero que te encuentres muy bien.\n\nLes escribo porque hace un tiempo no hemos recibido solicitudes de su parte y quería saber si están necesitando algún tipo de producto para este mes.\n\nQuedo atento,\nSaludos!'

VARIABLES_PLANTILLA = ('nombre', 'cliente', 'rubro')

CRM_LOGIN = 'https://crm.example.invalid'

CRM_CONTACTO = 'https://crm.example.invalid'

GMAIL_INBOX = 'https://mail.google.com/mail/u/0/#inbox'

GMAIL_COMPOSE = 'https://mail.google.com/mail/u/0/#inbox?compose=new'

GMAIL_LOGIN = 'https://accounts.google.com/ServiceLogin?service=mail&continue=https://mail.google.com/mail/u/0/%23inbox'

HEADLESS_ARG = '--headless=new'

UMBRAL_PDF_MB = 2.0

MAX_REINTENTOS_GMAIL = 2

ESPERA_POST_ENVIO = 6

ESPERA_LOGIN_GMAIL = 180

SEG_POR_CONTACTO_INICIAL = 40

PAUSA_LOTE_PROM = 240

RECICLAJE_CADA = 80

URLS_BLOQUEADAS_CRM = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg', '*.woff*', '*.ttf', '*google-analytics*', '*facebook*', '*doubleclick*']

RED_ESPERA_MAX = 300

RED_INTERVALO = 10

RED_MAX_REANUDACIONES = 3

ENCABEZADO_LOG = ['Fecha y Hora', 'ID Contacto', 'Nombre Cliente', 'Correo', 'Estado', 'Detalle / Error']

ESTADOS_PENDIENTES = ('ERROR', 'REVISAR', 'ENVIANDO', 'ENVIADO - FALLÓ', 'SIN CORREO')

CRM_CONTACTOS = 'https://crm.example.invalid'

XPATH_DESPLEGABLE_EJECUTIVO = "//*[@id='w0-filters']/td[9]/select"

XPATH_PAGINADOR_SIGUIENTE = "//*[@id='w0']//ul[contains(@class,'pagination')]//li[contains(@class,'next') and not(contains(@class,'disabled'))]/a | //*[@id='w0']//ul[contains(@class,'pagination')]//a[text()='»'] | //*[@id='w0']/div/div[6]/div[1]/ul/li[12]/a"

TAM_LOTE_DEFECTO = 50

UMBRAL_CACHE_MB = 400

CARPETAS_CACHE = ('Cache', 'Code Cache', 'GPUCache', 'GrShaderCache', 'ShaderCache', 'DawnCache')

XP_PARA = ['//input[@peoplekit-id]', "//input[@aria-label='Para' or @aria-label='To' or @aria-label='Destinatarios' or @aria-label='Recipients']", "//input[@role='combobox' and not(@name='subjectbox')]", "//textarea[@name='to']"]

XP_ASUNTO = ["//input[@name='subjectbox']"]

XP_CUERPO = ["//div[(@aria-label='Cuerpo del mensaje' or @aria-label='Message Body') and (@contenteditable='true' or @role='textbox')]"]

XP_BTN_ENVIAR = ["//div[@role='button' and (starts-with(@aria-label,'Enviar') or starts-with(@aria-label,'Send'))]", "//div[text()='Enviar' or text()='Send']"]

XP_DIALOGO = "//div[@role='dialog']"

XP_INPUT_ARCHIVO = ["//div[@role='dialog']//input[@type='file']", "//input[@type='file']"]

XP_CHIP_DEST = "//div[@role='dialog']//*[@email='{correo}' or @data-hovercard-id='{correo}']"

XP_BANDEJA = "//div[@role='main']"

JS_CARET_INICIO = '\nconst el = arguments[0]; el.focus();\nconst r = document.createRange(); r.setStart(el, 0); r.collapse(true);\nconst s = window.getSelection(); s.removeAllRanges(); s.addRange(r);\n'

JS_INSERTAR_LINEAS = "\nconst el = arguments[0], lineas = arguments[1];\nel.focus();\nfor (let i = 0; i < lineas.length; i++) {\n  if (i > 0) document.execCommand('insertParagraph', false, null);\n  if (lineas[i]) document.execCommand('insertText', false, lineas[i]);\n}\nreturn true;\n"

JS_ESTADO_ADJUNTO = "\nconst d = document.querySelector('div[role=dialog]') || document.body;\nreturn {texto: (d.innerText || '').toLowerCase(),\n        subiendo: d.querySelectorAll('[role=progressbar]').length};\n"

XP_CORREO_FICHA = ["//li[contains(@class,'list-group-item')][.//a[contains(@href,'edit-email')]]", "//ul[contains(@class,'list-group')][.//a[contains(@href,'add-email')]]/li[contains(@class,'list-group-item') and contains(., '@')]", '/html/body/div/div/div[1]/div/div[1]/div/div[2]/div[2]/div/div/div/div[2]/ul/li']

DOMINIOS_INTERNOS = ('@interno.example.invalid', '@organizacion.example.invalid')

REGEX_EMAIL = re.compile('^[a-z0-9._%+\\-]+@[a-z0-9\\-]+(?:\\.[a-z0-9\\-]+)*\\.[a-z]{2,}$')

TITULOS_NOMBRE = {'sra', 'sr', 'sres', 'don', 'dona', 'dra', 'dr', 'ma', 'm'}

NOMBRES_COMPUESTOS = {'maria', 'juan', 'ana', 'jose', 'luis'}

PALABRAS_INSTITUCIONALES = ('liceo', 'open', 'portal', 'inaltum', 'jefa', 'pago', 'facturacion', 'consulta', 'area', 'ejecutivo', 'compras')

SALUDO_GENERICO = 'Estimada/o'

_CONTROL_RE = re.compile('[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]')

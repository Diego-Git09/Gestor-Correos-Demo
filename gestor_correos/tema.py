"""Tema: código separado del archivo original; versión de demostración."""
import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from . import configuracion as _configuracion
from . import utilidades as _utilidades


BG = '#0a0e1a'

PANEL = '#111729'

PANEL2 = '#18213a'

BORDE = '#27345a'

TEXTO = '#e8eefc'

APAGADO = '#8c99ba'

ACENTO = '#00e5ff'

ACENTO_HOVER = '#66f0ff'

VIOLETA = '#8b5cf6'

VERDE = '#2ee6a0'

AMBAR = '#ffb84d'

ROJO = '#ff5a7a'

LOG_BG = '#060912'

LOG_TEXTO = '#c3cee6'

TEXTO_SOBRE_ACENTO = '#031219'

FUENTE_UI = 'Segoe UI' if _configuracion.ES_WINDOWS else 'Helvetica Neue' if _configuracion.ES_MAC else 'DejaVu Sans'

FUENTE_MONO = 'Consolas' if _configuracion.ES_WINDOWS else 'Menlo' if _configuracion.ES_MAC else 'DejaVu Sans Mono'

def fuente_ui(tam=10, peso='normal'):
    return (FUENTE_UI, tam, peso)

def _mezclar(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple((int(a[i] + (b[i] - a[i]) * t) for i in range(3)))

class BarraNeon(tk.Canvas):
    """Línea fina con degradado cian -> violeta."""

    def __init__(self, master, alto=3, fondo=BG):
        super().__init__(master, height=alto, bg=fondo, highlightthickness=0, bd=0)
        self.bind('<Configure>', self._dibujar)

    def _dibujar(self, evento):
        self.delete('all')
        ancho = max(evento.width, 1)
        pasos = min(ancho, 140)
        paso = ancho / pasos
        alto = max(self.winfo_height(), 1)
        for i in range(pasos):
            color = _mezclar(ACENTO, VIOLETA, i / max(pasos - 1, 1))
            self.create_rectangle(i * paso, 0, (i + 1) * paso + 1, alto, outline='', fill=color)

def aplicar_tema(root):
    root.configure(fg_color=BG) if isinstance(root, ctk.CTk) else root.configure(bg=BG)
    s = ttk.Style(root)
    s.theme_use('clam')
    s.configure('.', background=BG, foreground=TEXTO, fieldbackground=PANEL2, bordercolor=BORDE, lightcolor=BORDE, darkcolor=BORDE, troughcolor=PANEL2, font=fuente_ui(10), focuscolor=BG)
    s.configure('TFrame', background=BG)
    s.configure('Card.TFrame', background=PANEL)
    s.configure('TLabel', background=BG, foreground=TEXTO)
    s.configure('Card.TLabel', background=PANEL, foreground=TEXTO)
    s.configure('Muted.TLabel', background=BG, foreground=APAGADO, font=fuente_ui(9))
    s.configure('CardMuted.TLabel', background=PANEL, foreground=APAGADO, font=fuente_ui(9))
    s.configure('CardTitle.TLabel', background=PANEL, foreground=ACENTO, font=fuente_ui(9, 'bold'))
    s.configure('Title.TLabel', background=BG, foreground=TEXTO, font=fuente_ui(20, 'bold'))
    s.configure('Estado.TLabel', background=BG, foreground=TEXTO, font=fuente_ui(12, 'bold'))
    s.configure('Eta.TLabel', background=BG, foreground=ACENTO, font=fuente_ui(10))
    s.configure('TButton', background=PANEL2, foreground=TEXTO, bordercolor=BORDE, lightcolor=PANEL2, darkcolor=PANEL2, focuscolor=PANEL2, padding=(14, 8), relief='flat', borderwidth=1, font=fuente_ui(10))
    s.map('TButton', background=[('disabled', PANEL), ('pressed', BORDE), ('active', '#223055')], foreground=[('disabled', APAGADO)], bordercolor=[('active', ACENTO), ('disabled', BORDE)])
    s.configure('Accent.TButton', background=ACENTO, foreground=TEXTO_SOBRE_ACENTO, bordercolor=ACENTO, lightcolor=ACENTO, darkcolor=ACENTO, focuscolor=ACENTO, padding=(18, 11), font=fuente_ui(11, 'bold'))
    s.map('Accent.TButton', background=[('disabled', PANEL2), ('pressed', ACENTO), ('active', ACENTO_HOVER)], foreground=[('disabled', APAGADO)], bordercolor=[('active', ACENTO_HOVER), ('disabled', BORDE)], lightcolor=[('active', ACENTO_HOVER)], darkcolor=[('active', ACENTO_HOVER)])
    s.configure('Danger.TButton', background='#3a1626', foreground=ROJO, bordercolor=ROJO, lightcolor='#3a1626', darkcolor='#3a1626', focuscolor='#3a1626', padding=(16, 9), font=fuente_ui(10, 'bold'))
    s.map('Danger.TButton', background=[('disabled', PANEL2), ('pressed', '#7a2540'), ('active', '#5a1d33')], foreground=[('disabled', APAGADO)], bordercolor=[('disabled', BORDE)])
    s.configure('TEntry', fieldbackground=PANEL2, foreground=TEXTO, insertcolor=ACENTO, bordercolor=BORDE, lightcolor=BORDE, darkcolor=BORDE, padding=6)
    s.map('TEntry', bordercolor=[('focus', ACENTO)], lightcolor=[('focus', ACENTO)], darkcolor=[('focus', ACENTO)])
    s.configure('TCombobox', fieldbackground=PANEL2, background=PANEL2, foreground=TEXTO, arrowcolor=ACENTO, bordercolor=BORDE, lightcolor=BORDE, darkcolor=BORDE, insertcolor=ACENTO, padding=6)
    s.map('TCombobox', fieldbackground=[('readonly', PANEL2)], foreground=[('readonly', TEXTO)], bordercolor=[('focus', ACENTO)], background=[('active', PANEL2)])
    root.option_add('*TCombobox*Listbox.background', PANEL2)
    root.option_add('*TCombobox*Listbox.foreground', TEXTO)
    root.option_add('*TCombobox*Listbox.selectBackground', ACENTO)
    root.option_add('*TCombobox*Listbox.selectForeground', TEXTO_SOBRE_ACENTO)
    root.option_add('*TCombobox*Listbox.font', fuente_ui(10))
    s.configure('Card.TCheckbutton', background=PANEL, foreground=TEXTO, focuscolor=PANEL, indicatorbackground=PANEL2, indicatorforeground=TEXTO_SOBRE_ACENTO, upperbordercolor=BORDE, lowerbordercolor=BORDE, font=fuente_ui(10))
    s.map('Card.TCheckbutton', background=[('active', PANEL)], indicatorbackground=[('selected', ACENTO), ('!selected', PANEL2)], indicatorforeground=[('selected', TEXTO_SOBRE_ACENTO)])
    s.configure('Neon.Horizontal.TProgressbar', troughcolor=PANEL2, background=ACENTO, bordercolor=BORDE, lightcolor=ACENTO, darkcolor=ACENTO, thickness=12)
    s.configure('Treeview', background=PANEL, fieldbackground=PANEL, foreground=TEXTO, bordercolor=BORDE, lightcolor=PANEL, darkcolor=PANEL, rowheight=26, borderwidth=0)
    s.map('Treeview', background=[('selected', '#1f3a66')], foreground=[('selected', '#ffffff')])
    s.configure('Treeview.Heading', background=PANEL2, foreground=ACENTO, relief='flat', bordercolor=BORDE, lightcolor=PANEL2, darkcolor=PANEL2, padding=(8, 6), font=fuente_ui(9, 'bold'))
    s.map('Treeview.Heading', background=[('active', '#223055')])
    for orient in ('Vertical', 'Horizontal'):
        s.configure(f'{orient}.TScrollbar', background=PANEL2, troughcolor=BG, bordercolor=BG, lightcolor=PANEL2, darkcolor=PANEL2, arrowcolor=APAGADO, gripcount=0)
        s.map(f'{orient}.TScrollbar', background=[('active', BORDE)])
    s.configure('TSeparator', background=BORDE)

def tarjeta(parent, titulo):
    """Panel con borde fino y título. Devuelve (contenedor_externo, cuerpo): el cuerpo es donde se ponen los widgets."""
    borde = tk.Frame(parent, bg=BORDE, padx=1, pady=1)
    interior = ttk.Frame(borde, style='Card.TFrame', padding=(14, 10, 14, 12))
    interior.pack(fill='both', expand=True)
    ttk.Label(interior, text=titulo.upper(), style='CardTitle.TLabel').pack(anchor='w', pady=(0, 8))
    cuerpo = ttk.Frame(interior, style='Card.TFrame')
    cuerpo.pack(fill='both', expand=True)
    return (borde, cuerpo)

def campo_texto(parent, alto=8):
    """Cuadro de texto multilínea con el estilo del tema."""
    return tk.Text(parent, height=alto, width=40, wrap='word', undo=True, bg=PANEL2, fg=TEXTO, insertbackground=ACENTO, selectbackground='#1f3a66', selectforeground='#ffffff', relief='flat', bd=0, padx=10, pady=8, font=fuente_ui(10), highlightthickness=1, highlightbackground=BORDE, highlightcolor=ACENTO)

def crear_tabla(parent, columnas, anchos, selectmode='browse'):
    """Treeview con barras de desplazamiento y colores por estado. Devuelve (contenedor, tabla)."""
    cont = ttk.Frame(parent)
    tabla = ttk.Treeview(cont, columns=columnas, show='headings', selectmode=selectmode)
    for c in columnas:
        tabla.heading(c, text=c.capitalize())
        tabla.column(c, width=anchos.get(c, 120), anchor='w')
    sb_y = ttk.Scrollbar(cont, orient='vertical', command=tabla.yview)
    sb_x = ttk.Scrollbar(cont, orient='horizontal', command=tabla.xview)
    tabla.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    sb_y.pack(side='right', fill='y')
    sb_x.pack(side='bottom', fill='x')
    tabla.pack(side='left', fill='both', expand=True)
    tabla.tag_configure('rojo', foreground=ROJO)
    tabla.tag_configure('ambar', foreground=AMBAR)
    tabla.tag_configure('gris', foreground=APAGADO)
    return (cont, tabla)

def etiqueta_estado(estado):
    """Tupla de etiquetas (color) para una fila de tabla según el estado; vacía si no aplica."""
    e = str(estado).upper()
    if e.startswith('ERROR'):
        return ('rojo',)
    if e.startswith(('REVISAR', 'ENVIANDO', 'ENVIADO - FALLÓ')):
        return ('ambar',)
    if e.startswith('SIN CORREO'):
        return ('gris',)
    return ()

LOGO_OPACIDAD = 0.12

def ficha_stat(parent, titulo, color):
    """Pequeña tarjeta con un número grande. Devuelve (contenedor, etiqueta_del_numero)."""
    borde = tk.Frame(parent, bg=BORDE, padx=1, pady=1)
    interior = tk.Frame(borde, bg=PANEL)
    interior.pack(fill='both', expand=True)
    valor = tk.Label(interior, text='0', bg=PANEL, fg=color, font=fuente_ui(20, 'bold'))
    valor.pack(pady=(8, 0))
    tk.Label(interior, text=titulo.upper(), bg=PANEL, fg=APAGADO, font=fuente_ui(8, 'bold')).pack(pady=(0, 8))
    return (borde, valor)

def sonar_alerta(root, repeticiones=3):
    """Aviso acústico al terminar la campaña, según el sistema operativo.
    Nunca lanza excepciones: si no hay sonido disponible, usa la campana de Tk."""
    try:
        if _configuracion.ES_WINDOWS:
            import winsound
            for _ in range(repeticiones):
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                time.sleep(0.45)
            return
        if _configuracion.ES_MAC:
            sonido = '/System/Library/Sounds/Glass.aiff'
            if os.path.exists(sonido):
                for _ in range(repeticiones):
                    subprocess.call(['afplay', sonido], timeout=5)
                return
    except Exception as e:
        _utilidades.log_debug('sonido de aviso', e)
    try:
        for _ in range(repeticiones):
            root.bell()
            root.update_idletasks()
            time.sleep(0.35)
    except Exception:
        pass

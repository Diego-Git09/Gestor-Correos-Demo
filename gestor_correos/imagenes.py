"""Imagenes: código separado del archivo original; versión de demostración."""
import os
import tkinter as tk
from . import configuracion as _configuracion
from . import tema as _tema


def pillow_disponible():
    try:
        import PIL
        return True
    except ImportError:
        return False

def cargar_logo_chico():
    if not os.path.exists(_configuracion.LOGO_FILE):
        return None
    try:
        img = tk.PhotoImage(file=_configuracion.LOGO_FILE)
        factor = max(1, -(-img.width() // _configuracion.LOGO_MAX_ANCHO), -(-img.height() // _configuracion.LOGO_MAX_ALTO))
        return img.subsample(factor) if factor > 1 else img
    except Exception:
        return None

def construir_marca_de_agua(ancho, alto, fondo=_tema.LOG_BG):
    from PIL import Image, ImageTk
    img = Image.open(_configuracion.LOGO_FILE).convert('RGBA')
    escala = min(ancho * 0.9 / img.width, alto * 0.9 / img.height)
    nuevo = (max(1, int(img.width * escala)), max(1, int(img.height * escala)))
    img = img.resize(nuevo, Image.LANCZOS)
    alfa = img.getchannel('A').point(lambda v: int(v * _tema.LOGO_OPACIDAD))
    img.putalpha(alfa)
    rgb = tuple((int(fondo[i:i + 2], 16) for i in (1, 3, 5))) + (255,)
    base = Image.new('RGBA', img.size, rgb)
    base.alpha_composite(img)
    return ImageTk.PhotoImage(base.convert('RGB'))

class LogCanvas(tk.Canvas):
    COLORES = {'error': _tema.ROJO, 'aviso': _tema.AMBAR, 'ok': _tema.VERDE, 'debug': _tema.APAGADO}

    def __init__(self, master, fuente, con_logo, fondo=_tema.LOG_BG):
        super().__init__(master, bg=fondo, highlightthickness=0)
        self.fondo = fondo
        self.fuente = fuente
        self.con_logo = con_logo
        self.lineas = []
        self.desfase = 0
        self.visibles = 1
        self.sb = None
        self._foto = None
        self._job = None
        self.bind('<Configure>', lambda e: self._programar())
        self.bind('<MouseWheel>', lambda e: self._mover(3 if e.delta > 0 else -3))
        self.bind('<Button-4>', lambda e: self._mover(3))
        self.bind('<Button-5>', lambda e: self._mover(-3))

    def _programar(self):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(120, self._refrescar)

    def _refrescar(self):
        self._job = None
        self._poner_logo()
        self._dibujar()

    def _poner_logo(self):
        if not self.con_logo:
            return
        w, h = (self.winfo_width(), self.winfo_height())
        if w < 50 or h < 50:
            return
        try:
            self._foto = construir_marca_de_agua(w, h, self.fondo)
        except Exception:
            self.con_logo = False
            return
        self.delete('logo')
        self.create_image(w // 2, h // 2, image=self._foto, tags='logo')
        self.tag_lower('logo')

    def agregar(self, linea, tag=None):
        self.lineas.append((linea, tag))
        if len(self.lineas) > 3000:
            del self.lineas[:500]
        if self.desfase > 0:
            self.desfase = min(self.desfase + 1, len(self.lineas) - 1)
        self._dibujar()

    def _dibujar(self):
        self.delete('txt')
        w, h = (self.winfo_width(), self.winfo_height())
        if w < 50 or h < 20:
            return
        y = h - 6
        i = len(self.lineas) - 1 - self.desfase
        ultimo = i
        while i >= 0 and y > 0:
            texto, tag = self.lineas[i]
            item = self.create_text(10, y, text=texto if texto else ' ', anchor='sw', width=w - 28, font=self.fuente, fill=self.COLORES.get(tag, _tema.LOG_TEXTO), tags='txt')
            y = self.bbox(item)[1]
            i -= 1
        self.visibles = max(1, ultimo - i)
        self._actualizar_barra()

    def _actualizar_barra(self):
        if not self.sb:
            return
        total = max(1, len(self.lineas))
        fin = (total - self.desfase) / total
        ini = max(0.0, (total - self.desfase - self.visibles) / total)
        self.sb.set(ini, fin)

    def _mover(self, n):
        self.desfase = max(0, min(self.desfase + n, max(0, len(self.lineas) - 1)))
        self._dibujar()

    def mover_barra(self, *args):
        if args[0] == 'scroll':
            paso = int(args[1]) * (3 if args[2] == 'units' else self.visibles)
            self._mover(-paso)
        elif args[0] == 'moveto':
            total = max(1, len(self.lineas))
            self.desfase = max(0, min(int(total - self.visibles - float(args[1]) * total), total - 1))
            self._dibujar()

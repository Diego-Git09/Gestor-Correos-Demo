"""Inicio del formulario original con adaptadores locales de demostración."""
from .formulario import lanzar_gui


class AplicacionDemo:
    """Expone los controles del formulario para las pruebas de interfaz."""
    def __init__(self, root):
        self.root = root
        self.controles = lanzar_gui(root=root, ejecutar_bucle=False)

    def vista_previa(self):
        self.controles['vista_previa']()

    def simular(self):
        self.controles['simular']()


def iniciar():
    lanzar_gui()

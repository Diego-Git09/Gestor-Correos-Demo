"""Interfaz del portafolio: datos ficticios y simulación local."""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import demostracion as demo


class AplicacionDemo:
    def __init__(self, root):
        self.root = root
        self.contactos = demo.cargar_ejemplos()
        self.resultados = []
        self.pdf = None
        root.title('Gestor de correos · Demostración local')
        root.geometry('1020x790')
        root.minsize(780, 640)
        root.configure(bg='#0a0e1a')
        estilo = ttk.Style(root)
        estilo.theme_use('clam')
        estilo.configure('TFrame', background='#0a0e1a')
        estilo.configure('TLabel', background='#0a0e1a', foreground='#e8eefc', font=('DejaVu Sans', 10))
        estilo.configure('Titulo.TLabel', foreground='#00e5ff', font=('DejaVu Sans', 23, 'bold'))
        estilo.configure('Treeview', background='#111729', fieldbackground='#111729', foreground='#e8eefc', rowheight=28)
        estilo.map('Treeview', background=[('selected', '#245366')])
        panel = ttk.Frame(root, padding=22)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='GESTOR DE CORREOS', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(panel, text='DEMO LOCAL · Contactos ficticios · No se envían correos ni se accede a cuentas').pack(anchor='w', pady=(5, 18))
        ttk.Label(panel, text='1. Selecciona contactos (Ctrl o Shift permite elegir varios)').pack(anchor='w')
        self.tabla = ttk.Treeview(panel, columns=('cliente', 'correo', 'estado'), show='headings', height=5, selectmode='extended')
        for columna, ancho in [('cliente', 250), ('correo', 300), ('estado', 190)]:
            self.tabla.heading(columna, text=columna.capitalize())
            self.tabla.column(columna, width=ancho)
        self.tabla.pack(fill='x', pady=(6, 14))
        for c in self.contactos:
            self.tabla.insert('', 'end', iid=c['ID'], values=(c['Cliente'], c['Correo'] or 'Sin correo', 'Por simular'))
        self.tabla.selection_set(self.tabla.get_children())
        ttk.Label(panel, text='2. Personaliza el mensaje · Variables: {nombre}, {cliente}, {rubro}').pack(anchor='w')
        self.asunto = tk.StringVar(root, value=demo.ASUNTO)
        ttk.Entry(panel, textvariable=self.asunto).pack(fill='x', pady=(6, 8))
        self.mensaje = tk.Text(panel, height=7, bg='#111729', fg='#e8eefc', insertbackground='#00e5ff', font=('DejaVu Sans', 11), wrap='word')
        self.mensaje.insert('1.0', demo.CUERPO)
        self.mensaje.pack(fill='both', expand=True)
        botones = ttk.Frame(panel)
        botones.pack(fill='x', pady=12)
        ttk.Button(botones, text='Adjuntar PDF', command=self.elegir_pdf).pack(side='left')
        ttk.Button(botones, text='Ver mensaje', command=self.vista_previa).pack(side='left', padx=8)
        ttk.Button(botones, text='Simular campaña', command=self.simular).pack(side='left')
        self.exportar = ttk.Button(botones, text='Exportar reporte', command=self.guardar_reporte, state='disabled')
        self.exportar.pack(side='right')
        self.adjunto = ttk.Label(panel, text='PDF: ninguno')
        self.adjunto.pack(anchor='w')
        self.estado = ttk.Label(panel, text='Listo para simular. No se necesitan credenciales.')
        self.estado.pack(anchor='w', pady=(10, 6))
        self.salida = tk.Text(panel, height=7, bg='#060912', fg='#c3cee6', wrap='word', state='disabled')
        self.salida.pack(fill='both', expand=True)

    def preparar(self):
        seleccion = set(self.tabla.selection())
        filas = [c for c in self.contactos if c['ID'] in seleccion]
        return demo.preparar_demostracion(filas, self.asunto.get(), self.mensaje.get('1.0', 'end-1c'), self.pdf)

    def mostrar(self, texto):
        self.salida.configure(state='normal')
        self.salida.delete('1.0', 'end')
        self.salida.insert('1.0', texto)
        self.salida.configure(state='disabled')

    def vista_previa(self):
        try:
            r = self.preparar()[0]
            self.mostrar(f'Para: {r.correo or "Sin correo"}\nAsunto: {r.asunto}\n\n{r.cuerpo}\n\nAdjunto: {r.adjunto or "ninguno"}')
        except (ValueError, OSError) as error:
            messagebox.showerror('Revisa los datos', str(error), parent=self.root)

    def simular(self):
        try:
            resultados = self.preparar()
        except (ValueError, OSError) as error:
            messagebox.showerror('Revisa los datos', str(error), parent=self.root)
            return
        self.resultados = resultados
        for r in resultados:
            self.tabla.set(r.id_contacto, 'estado', r.estado)
        datos = demo.resumen(resultados)
        self.estado.configure(text=f"Terminó: {datos['simulados']} simulados · {datos['omitidos']} omitidos · 0 envíos reales")
        self.mostrar('\n'.join(f'{r.cliente}: {r.estado}' for r in resultados))
        self.exportar.configure(state='normal')

    def elegir_pdf(self):
        ruta = filedialog.askopenfilename(parent=self.root, filetypes=[('Documentos PDF', '*.pdf')])
        if not ruta:
            return
        try:
            info = demo.comprobar_pdf(ruta)
        except Exception:
            messagebox.showerror('PDF no válido', 'No se pudo abrir ese PDF. Elige uno válido, sin cifrar y de hasta 20 MiB.', parent=self.root)
            return
        self.pdf = ruta
        self.adjunto.configure(text=f"PDF: {info['nombre']} · {info['paginas']} página(s)")

    def guardar_reporte(self):
        if not self.resultados:
            return
        ruta = filedialog.asksaveasfilename(parent=self.root, defaultextension='.json', initialfile='reporte_demo.json', filetypes=[('Reporte JSON', '*.json')])
        if ruta:
            try:
                demo.exportar_reporte(ruta, self.resultados)
            except OSError:
                messagebox.showerror('No se guardó', 'Elige un nombre nuevo en una carpeta con permiso de escritura.', parent=self.root)
            else:
                self.estado.configure(text='Reporte de simulación guardado. No se enviaron correos.')


def iniciar():
    root = tk.Tk()
    AplicacionDemo(root)
    root.mainloop()


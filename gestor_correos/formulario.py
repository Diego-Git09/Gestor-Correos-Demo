"""Formulario: código separado del archivo original; versión de demostración."""
import os
import time
import queue
import threading
import traceback
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from . import configuracion as _configuracion
from . import contactos as _contactos
from . import adaptadores_demo as _credenciales
from . import adaptadores_demo as _crm
from . import eventos as _eventos
from . import adaptadores_demo as _demo
from . import persistencia as _persistencia
from . import plantillas as _plantillas
from . import progreso as _progreso
from . import reportes as _reportes
from . import tema as _tema
from . import utilidades as _utilidades


def lanzar_gui(root=None, ejecutar_bucle=True):
    """Formulario original conectado exclusivamente a servicios de demostración."""
    _demo.preparar_entorno()
    ctk.set_appearance_mode('dark')
    if _configuracion.ES_WINDOWS:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Demo.GestorCorreos.1.0')
        except Exception:
            pass
    root = root if root is not None else ctk.CTk()

    def _error_ui(exc, val, tb):
        texto = ''.join(traceback.format_exception(exc, val, tb))
        try:
            carpeta = os.path.join(_configuracion.BASE_DIR, 'logs_ejecucion')
            os.makedirs(carpeta, exist_ok=True)
            with open(os.path.join(carpeta, 'errores_ui.log'), 'a', encoding='utf-8') as f:
                f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}\n{texto}\n')
        except Exception:
            pass
        messagebox.showerror('Error inesperado', f'{val}\n\nDetalle en logs_ejecucion/errores_ui.log')
    root.report_callback_exception = _error_ui
    try:
        try:
            from PIL import Image, ImageTk
            with Image.open(_configuracion.LOGO_FILE) as imagen:
                foto_icono = ImageTk.PhotoImage(imagen.copy())
        except Exception:
            foto_icono = tk.PhotoImage(file=_configuracion.LOGO_FILE)
        root.iconphoto(False, foto_icono)
        root.foto_icono = foto_icono
    except Exception:
        pass
    root.title(f'Automatización Correos Demo v{_configuracion.VERSION} ({_configuracion.NOMBRE_SO})')
    root.geometry('680x860')
    root.minsize(640, 740)
    root.resizable(True, True)
    _tema.aplicar_tema(root)
    cfg = _persistencia.cargar_config()
    huella_campana_guardada = cfg.get('huella_campana') or _reportes.huella_plantilla(cfg.get('asunto') or _configuracion.ASUNTO_CORREO_DEFECTO, cfg.get('cuerpo') or _configuracion.CUERPO_CORREO_DEFECTO)
    entorno = _credenciales.credenciales_manager_desde_entorno()
    try:
        guardadas = _credenciales.recuperar_credenciales()
        if guardadas:
            entorno = guardadas
    except Exception:
        messagebox.showwarning('Credenciales', 'No se pudieron recuperar las credenciales. Ingrésalas nuevamente.', parent=root)
    recordar_var = tk.BooleanVar(value=False)
    ejecutivo_var = tk.StringVar(value=_demo.EJECUTIVO)
    ruta_pdf_var = tk.StringVar(value=cfg.get('ruta_pdf') or '')
    headless_var = tk.BooleanVar(value=True)
    dry_run_var = tk.BooleanVar(value=True)
    asunto_var = tk.StringVar(value=cfg.get('asunto') or _configuracion.ASUNTO_CORREO_DEFECTO)
    asunto_gestion_var = tk.StringVar(value=cfg.get('asunto_gestion') or _configuracion.ASUNTO_GESTION)
    reintento_confirmado_id = None
    solo_gestion_id = None
    solo_ids = set()
    log_destino = None
    reintento_preparado = False
    cab = ttk.Frame(root, padding=(24, 18, 24, 6))
    cab.pack(fill='x')
    ttk.Label(cab, text='Demo · MAILBOT', style='Title.TLabel').pack(anchor='w')
    ttk.Label(cab, text=f'DEMO LOCAL · Sin cuentas ni envíos reales · {_configuracion.NOMBRE_SO}', style='Muted.TLabel').pack(anchor='w')
    _tema.BarraNeon(root, 3).pack(fill='x', padx=24, pady=(6, 8))
    pie = ttk.Frame(root, padding=(24, 10, 24, 18))
    pie.pack(side='bottom', fill='x')
    body = ttk.Frame(root, padding=(24, 4, 24, 0))
    body.pack(fill='both', expand=True)
    body.columnconfigure(0, weight=1)
    body.rowconfigure(1, weight=1)
    fila1 = ttk.Frame(body)
    fila1.grid(row=0, column=0, sticky='ew', pady=(0, 10))
    fila1.columnconfigure(0, weight=1, uniform='fila1')
    fila1.columnconfigure(1, weight=1, uniform='fila1')
    b_mgr, c_mgr = _tema.tarjeta(fila1, 'Manager · Datos ficticios')
    b_mgr.grid(row=0, column=0, sticky='nsew', padx=(0, 6))
    c_mgr.columnconfigure(1, weight=1)
    ttk.Label(c_mgr, text='Usuario', style='Card.TLabel').grid(row=0, column=0, sticky='w', pady=4)
    entry_user_crm = ttk.Entry(c_mgr, width=16)
    if entorno.get('user'):
        entry_user_crm.insert(0, entorno['user'])
    entry_user_crm.configure(state='disabled')
    entry_user_crm.grid(row=0, column=1, sticky='ew', padx=(12, 0), pady=4)
    ttk.Label(c_mgr, text='Contraseña', style='Card.TLabel').grid(row=1, column=0, sticky='w', pady=4)
    entry_pass_crm = ttk.Entry(c_mgr, width=16, show='*')
    if entorno.get('password'):
        entry_pass_crm.insert(0, entorno['password'])
    entry_pass_crm.configure(state='disabled')
    entry_pass_crm.grid(row=1, column=1, sticky='ew', padx=(12, 0), pady=4)
    ttk.Label(c_mgr, text='Nombre Ejecutivo CRM', style='Card.TLabel').grid(row=2, column=0, sticky='w')
    ctk.CTkEntry(c_mgr, textvariable=ejecutivo_var, bg_color=_tema.PANEL, state='disabled').grid(row=2, column=1, sticky='ew', padx=(12, 0), pady=4)

    def persistir_identidad(*_):
        try:
            _credenciales.guardar_identidad(entry_user_crm.get().strip(), entry_pass_crm.get(), recordar_var.get(), ejecutivo_var.get().strip())
            return True
        except Exception:
            messagebox.showerror('Credenciales', 'No se pudo guardar en el almacén seguro del sistema. Desmarca Recordar credenciales o habilita el llavero del sistema.', parent=root)
            return False
    ejecutivo_var.trace_add('write', lambda *_: _persistencia.actualizar_config({'nombre_ejecutivo': ejecutivo_var.get().strip()}))
    ctk.CTkCheckBox(c_mgr, text='Recordar credenciales (desactivado)', variable=recordar_var, state='disabled', bg_color=_tema.PANEL, command=persistir_identidad).grid(row=3, column=0, columnspan=2, sticky='w', pady=5)
    entry_user_crm.bind('<FocusOut>', persistir_identidad)
    entry_pass_crm.bind('<FocusOut>', persistir_identidad)

    def al_cerrar_formulario():
        if sincronizando[0]:
            messagebox.showinfo('Sincronización', 'Espera a que termine la sincronización antes de cerrar.', parent=root)
            return
        if persistir_identidad():
            root.destroy()
    root.protocol('WM_DELETE_WINDOW', al_cerrar_formulario)
    b_rng, c_rng = _tema.tarjeta(fila1, 'Rango de contactos')
    b_rng.grid(row=0, column=1, sticky='nsew', padx=(6, 0))
    c_rng.columnconfigure(1, weight=1)
    ttk.Label(c_rng, text='Desde N°', style='Card.TLabel').grid(row=0, column=0, sticky='w', pady=4)
    entry_inicio = ttk.Entry(c_rng, width=8)
    sugerencia = _reportes.sugerir_rango(cfg.get('tam_lote'))
    entry_inicio.insert(0, str(sugerencia['inicio']) if sugerencia and sugerencia['inicio'] else '1')
    entry_inicio.grid(row=0, column=1, sticky='w', padx=(12, 0), pady=4)
    ttk.Label(c_rng, text='Hasta N°', style='Card.TLabel').grid(row=1, column=0, sticky='w', pady=4)
    entry_fin = ttk.Entry(c_rng, width=8)
    entry_fin.insert(0, str(sugerencia['fin']) if sugerencia and sugerencia['fin'] else str(len(_contactos.cargar_contactos())))
    entry_fin.grid(row=1, column=1, sticky='w', padx=(12, 0), pady=4)
    lbl_avance = ttk.Label(c_rng, text='Sin avance previo', style='CardMuted.TLabel')
    lbl_avance.grid(row=2, column=0, columnspan=2, sticky='w', pady=(2, 0))
    if sugerencia:
        lbl_avance.config(text=f"✔ {sugerencia['hechos']} de {sugerencia['total']} con estado" if sugerencia['inicio'] else '✔ Todos los contactos ya tienen estado')
    b_msg, c_msg = _tema.tarjeta(body, 'Mensaje')
    b_msg.grid(row=1, column=0, sticky='nsew', pady=(0, 10))
    c_msg.columnconfigure(0, weight=1)
    c_msg.rowconfigure(3, weight=1)
    ttk.Label(c_msg, text='Asunto del correo', style='Card.TLabel').grid(row=0, column=0, sticky='w')
    entry_asunto = ttk.Entry(c_msg, textvariable=asunto_var)
    entry_asunto.grid(row=1, column=0, sticky='ew', pady=(3, 8))
    ttk.Label(c_msg, text='Cuerpo del correo', style='Card.TLabel').grid(row=2, column=0, sticky='w')
    cont_cuerpo = tk.Frame(c_msg, bg=_tema.PANEL)
    cont_cuerpo.grid(row=3, column=0, sticky='nsew', pady=(3, 4))
    txt_cuerpo = _tema.campo_texto(cont_cuerpo, alto=8)
    sb_cuerpo = ttk.Scrollbar(cont_cuerpo, command=txt_cuerpo.yview)
    txt_cuerpo.configure(yscrollcommand=sb_cuerpo.set)
    sb_cuerpo.pack(side='right', fill='y')
    txt_cuerpo.pack(side='left', fill='both', expand=True)
    txt_cuerpo.insert('1.0', cfg.get('cuerpo') or _configuracion.CUERPO_CORREO_DEFECTO)
    ttk.Label(c_msg, text='Variables que se reemplazan por los datos de cada contacto: {nombre}  {cliente}  {rubro}. Los mensajes solo se simulan; no se utiliza Gmail.', style='CardMuted.TLabel', wraplength=560, justify='left').grid(row=4, column=0, sticky='w', pady=(0, 8))
    ttk.Label(c_msg, text='Asunto de la gestión (Manager)', style='Card.TLabel').grid(row=5, column=0, sticky='w')
    ttk.Entry(c_msg, textvariable=asunto_gestion_var).grid(row=6, column=0, sticky='ew', pady=(3, 8))
    b_dat, c_dat = _tema.tarjeta(body, 'Datos, adjuntos y opciones')
    b_dat.grid(row=2, column=0, sticky='ew')
    c_dat.columnconfigure(1, weight=1)

    def leer_textos():
        asunto = _utilidades.sanitizar_texto(asunto_var.get()).strip()
        cuerpo = _utilidades.sanitizar_texto(txt_cuerpo.get('1.0', 'end').replace('\r\n', '\n')).strip()
        return (asunto, cuerpo)

    def vista_previa():
        asunto, cuerpo = leer_textos()
        ejemplo = {'nombre': 'Carlos', 'cliente': 'EMPRESA DE EJEMPLO S.A.', 'rubro': 'Educación'}
        messagebox.showinfo('Vista previa (con datos de ejemplo)', f'Asunto:\n{_plantillas.renderizar_plantilla(asunto, ejemplo)}\n\nCuerpo:\n{_plantillas.renderizar_plantilla(cuerpo, ejemplo)}')

    def restaurar_texto():
        if messagebox.askyesno('Restaurar', '¿Volver al asunto y cuerpo originales?'):
            asunto_var.set(_configuracion.ASUNTO_CORREO_DEFECTO)
            txt_cuerpo.delete('1.0', 'end')
            txt_cuerpo.insert('1.0', _configuracion.CUERPO_CORREO_DEFECTO)

    def abrir_revision_pendientes():
        try:
            pendientes = _reportes.cargar_contactos_pendientes_revision()
        except Exception as error:
            messagebox.showerror('No se pudieron cargar los pendientes', str(error), parent=root)
            return
        if not pendientes:
            messagebox.showinfo('Revisión de pendientes', 'No hay contactos pendientes de revisión.', parent=root)
            return
        win = tk.Toplevel(root)
        win.configure(bg=_tema.BG)
        win.title(f'Revisión de pendientes ({len(pendientes)})')
        win.geometry('1180x440')
        win.minsize(760, 320)
        win.transient(root)
        marco = ttk.Frame(win, padding=16)
        marco.pack(fill='both', expand=True)
        ttk.Label(marco, text='Selecciona uno o varios contactos (Ctrl/Cmd o Shift + clic) de una misma campaña. Si el correo pudo haberse enviado, verifica Gmail > Enviados antes de autorizar el reintento.', wraplength=1130, style='Muted.TLabel').pack(anchor='w', pady=(0, 10))
        columnas = ('campana', 'fila', 'id', 'nombre', 'correo', 'estado', 'detalle')
        anchos = {'campana': 190, 'fila': 55, 'id': 75, 'nombre': 150, 'correo': 190, 'estado': 190, 'detalle': 350}
        cont, tabla = _tema.crear_tabla(marco, columnas, anchos, selectmode='extended')
        cont.pack(fill='both', expand=True)
        pendientes_por_iid = {}
        for numero, pendiente in enumerate(pendientes, start=1):
            iid = str(numero)
            pendientes_por_iid[iid] = pendiente
            tabla.insert('', 'end', iid=iid, tags=_tema.etiqueta_estado(pendiente['estado']), values=(pendiente['campana'], pendiente['fila'], pendiente['id'], pendiente['nombre'], pendiente['correo'], pendiente['estado'], pendiente['detalle']))

        def preparar_reintento():
            nonlocal reintento_confirmado_id, solo_gestion_id, log_destino, reintento_preparado, solo_ids
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning('Selecciona contactos', 'Selecciona al menos un contacto de la lista.', parent=win)
                return
            elegidos = [pendientes_por_iid[i] for i in seleccion]
            if len({p['ruta'] for p in elegidos}) > 1:
                messagebox.showwarning('Campañas distintas', 'Los contactos seleccionados pertenecen a campañas distintas. Prepara por separado los de cada campaña.', parent=win)
                return
            sin_gestion = [p for p in elegidos if p['estado'].upper().startswith('ENVIADO - FALLÓ')]
            reenvio = [p for p in elegidos if p not in sin_gestion]
            pregunta = f'Se prepararán {len(elegidos)} contacto(s): {len(reenvio)} con reenvío y {len(sin_gestion)} solo gestión.\n\nPara los de reenvío, confirma en Gmail > Enviados que NO recibieron el correo. Para los de solo gestión, confirma en el Manager que la gestión no exista (el correo ya salió y no se reenvía).\n\nCorrige primero la causa indicada en cada uno. ¿Continuar?'
            if reenvio and elegidos[0]['campana'] != 'Campaña activa':
                pregunta += '\n\nEl reporte archivado no guarda el asunto ni el cuerpo originales. Se usarán los textos que están ahora en el formulario.'
            if not messagebox.askyesno('Confirmar revisión', pregunta, parent=win):
                return
            filas = [p['fila'] for p in elegidos]
            entry_inicio.delete(0, 'end')
            entry_inicio.insert(0, str(min(filas)))
            entry_fin.delete(0, 'end')
            entry_fin.insert(0, str(max(filas)))
            reintento_confirmado_id = {p['id'] for p in reenvio}
            solo_gestion_id = {p['id'] for p in sin_gestion}
            solo_ids = {p['id'] for p in elegidos}
            log_destino = None if elegidos[0]['campana'] == 'Campaña activa' else elegidos[0]['ruta']
            reintento_preparado = True
            win.destroy()
            aviso_prueba = '\n\nEl modo prueba está activo. Desactívalo antes de iniciar para ejecutar el reintento real.' if dry_run_var.get() else ''
            messagebox.showinfo('Contactos preparados', f'{len(elegidos)} contacto(s) listos. Revisa o corrige el asunto, cuerpo o datos y pulsa Iniciar. Solo se procesarán los seleccionados.{aviso_prueba}', parent=root)
        botones_revision = ttk.Frame(marco)
        botones_revision.pack(fill='x', pady=(10, 0))
        ttk.Button(botones_revision, text='Cerrar', command=win.destroy).pack(side='right')
        ttk.Button(botones_revision, text='Preparar reintento', style='Accent.TButton', command=preparar_reintento).pack(side='right', padx=8)
    fila_botones = ttk.Frame(c_msg, style='Card.TFrame')
    fila_botones.grid(row=7, column=0, sticky='w')
    ttk.Button(fila_botones, text='👁  Vista previa', command=vista_previa).pack(side='left')
    ttk.Button(fila_botones, text='↺  Restaurar original', command=restaurar_texto).pack(side='left', padx=8)
    ttk.Button(fila_botones, text='Pendientes (no aplica a demo)', state='disabled', command=abrir_revision_pendientes).pack(side='left')
    sincronizando = [False]
    cola_sync = queue.Queue()

    def iniciar_sincronizacion():
        if sincronizando[0]:
            return
        usuario, password, ejecutivo = (entry_user_crm.get().strip(), entry_pass_crm.get(), ejecutivo_var.get().strip())
        if not usuario or not password or (not ejecutivo):
            messagebox.showwarning('Datos incompletos', 'Ingresa usuario, contraseña y Nombre Ejecutivo CRM.', parent=root)
            return
        if not persistir_identidad():
            return
        sincronizando[0] = True
        btn_sync.configure(state='disabled')
        _eventos.DETENER.clear()
        headless = headless_var.get()

        def trabajo():
            try:
                contactos = _crm.sincronizar_contactos_crm(usuario, password, ejecutivo, headless, lambda texto: cola_sync.put(('progreso', texto)))
                cola_sync.put(('fin', len(contactos)))
            except Exception as error:
                try:
                    carpeta = os.path.join(_configuracion.BASE_DIR, 'logs_ejecucion')
                    os.makedirs(carpeta, exist_ok=True)
                    with open(os.path.join(carpeta, 'errores_sync.log'), 'a', encoding='utf-8') as f:
                        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}\n{traceback.format_exc()}\n')
                except Exception:
                    pass
                cola_sync.put(('error', f'{error}\n\nDetalle en logs_ejecucion/errores_sync.log'))
        threading.Thread(target=trabajo, daemon=True).start()
        root.after(100, consultar_sincronizacion)

    def consultar_sincronizacion():
        try:
            while True:
                tipo, valor = cola_sync.get_nowait()
                if tipo == 'progreso':
                    lbl_base.config(text=valor)
                else:
                    sincronizando[0] = False
                    btn_sync.configure(state='normal')
                    if tipo == 'fin':
                        lbl_base.config(text=f'{valor} contactos sincronizados', foreground=_tema.VERDE)
                        entry_inicio.delete(0, 'end')
                        entry_inicio.insert(0, '1')
                        entry_fin.delete(0, 'end')
                        entry_fin.insert(0, str(valor))
                        root.bell()
                        messagebox.showinfo('Sincronización completada', f'Base de ejemplo cargada: {valor} contactos ficticios. No se accedió a Internet.', parent=root)
                    else:
                        lbl_base.config(text='Sincronización fallida', foreground=_tema.ROJO)
                        messagebox.showerror('Sincronización', valor, parent=root)
        except queue.Empty:
            pass
        if sincronizando[0]:
            root.after(100, consultar_sincronizacion)

    def seleccionar_pdf():
        archivo = filedialog.askopenfilename(title='Seleccionar archivo PDF para adjuntar', filetypes=[('Archivos PDF', '*.pdf')])
        if archivo:
            ruta_pdf_var.set(archivo)
            lbl_pdf_estado.config(text=f'📎 {os.path.basename(archivo)}', foreground=_tema.VERDE)
            _persistencia.guardar_config(asunto_var.get(), txt_cuerpo.get('1.0', 'end').replace('\r\n', '\n').strip(), asunto_gestion_var.get(), ruta_pdf=archivo)
        else:
            ruta_pdf_var.set('')
            lbl_pdf_estado.config(text='Sin PDF adjunto', foreground=_tema.APAGADO)
    btn_sync = ctk.CTkButton(c_dat, text='🔄 Cargar base de ejemplo', command=iniciar_sincronizacion, bg_color=_tema.PANEL)
    btn_sync.grid(row=0, column=0, sticky='w', pady=(0, 6))
    lbl_base = ttk.Label(c_dat, text='Contactos ficticios del proyecto', style='Card.TLabel', wraplength=280)
    lbl_base.grid(row=0, column=1, sticky='w', padx=12)
    if os.path.exists(_configuracion.CONTACTOS_FILE):
        try:
            lbl_base.config(text=f'{len(_contactos.cargar_contactos())} contactos guardados', foreground=_tema.VERDE)
        except Exception:
            lbl_base.config(text='Base JSON inválida; sincroniza nuevamente', foreground=_tema.ROJO)
    ttk.Button(c_dat, text='📁  Seleccionar PDF (opcional)', command=seleccionar_pdf).grid(row=2, column=0, sticky='w', pady=(0, 8))
    lbl_pdf_estado = ttk.Label(c_dat, text='Sin PDF adjunto', style='Card.TLabel', foreground=_tema.APAGADO, font=_tema.fuente_ui(9, 'italic'))
    lbl_pdf_estado.grid(row=2, column=1, sticky='w', padx=12, pady=(0, 8))
    if ruta_pdf_var.get():
        lbl_pdf_estado.config(text=f'📎 {os.path.basename(ruta_pdf_var.get())}', foreground=_tema.VERDE)
    ttk.Checkbutton(c_dat, text='Ejecutar en segundo plano (sin ventanas)', variable=headless_var, state='disabled', style='Card.TCheckbutton').grid(row=3, column=0, columnspan=2, sticky='w', pady=2)
    ttk.Checkbutton(c_dat, text='Modo prueba (sin envíos ni gestiones reales)', variable=dry_run_var, state='disabled', style='Card.TCheckbutton').grid(row=4, column=0, columnspan=2, sticky='w', pady=2)

    def al_presionar_iniciar():
        nonlocal huella_campana_guardada, reintento_confirmado_id, solo_gestion_id, log_destino, reintento_preparado, solo_ids
        if not os.path.isfile(_configuracion.CONTACTOS_FILE):
            messagebox.showwarning('Base de datos no adjuntada', 'Sincroniza primero tu cartera desde el Manager CRM.', parent=root)
            return
        if sincronizando[0]:
            messagebox.showinfo('Sincronización', 'Espera a que termine la sincronización.', parent=root)
            return
        try:
            _contactos.validar_cartera(ejecutivo_var.get())
        except Exception as error:
            messagebox.showerror('Cartera', str(error), parent=root)
            return
        if not persistir_identidad():
            return
        u_crm = entry_user_crm.get().strip()
        p_crm = entry_pass_crm.get()
        try:
            i_idx = int(entry_inicio.get().strip())
            f_idx = int(entry_fin.get().strip())
        except ValueError:
            messagebox.showerror('Error', 'Los rangos deben ser números enteros.')
            return
        if not u_crm or not p_crm:
            messagebox.showwarning('Atención', 'Por favor ingresa tus credenciales del Manager.')
            return
        asunto, cuerpo = leer_textos()
        if not asunto or not cuerpo:
            messagebox.showwarning('Atención', 'El asunto y el cuerpo del correo no pueden estar vacíos.')
            return
        asunto_gestion = asunto_gestion_var.get().strip()
        if not asunto_gestion:
            messagebox.showwarning('Atención', 'El asunto de la gestión no puede estar vacío.')
            return
        raras = _plantillas.variables_desconocidas(asunto, cuerpo)
        if raras:
            lista = ', '.join(('{' + v + '}' for v in raras))
            if not messagebox.askyesno('Variables no reconocidas', f'El texto contiene {lista}, que el bot no reconoce y enviaría tal cual.\n\nLas variables válidas son {{nombre}}, {{cliente}} y {{rubro}} (en minúsculas).\n\n¿Quieres continuar de todos modos?'):
                return
        if ruta_pdf_var.get() and (not os.path.isfile(ruta_pdf_var.get())):
            messagebox.showwarning('PDF no encontrado', f'No se encuentra el PDF guardado:\n{ruta_pdf_var.get()}\n\nSelecciónalo otra vez o quita la ruta antes de iniciar.', parent=root)
            return
        try:
            texto_resumen = _demo.resumen_previo(i_idx, f_idx, solo_ids)
        except ValueError as error:
            messagebox.showerror('Rango no válido', str(error), parent=root)
            return
        if not messagebox.askyesno('Confirmar inicio', texto_resumen + '\n\n¿Iniciar?', parent=root):
            return
        huella_actual = _reportes.huella_plantilla(asunto, cuerpo)
        cambio_texto = huella_actual != huella_campana_guardada
        if not reintento_preparado and (not dry_run_var.get()):
            try:
                if _reportes.preparar_campana(_contactos.cargar_contactos()):
                    i_idx, f_idx = (1, len(_contactos.cargar_contactos()))
                    messagebox.showinfo('Nueva campaña', '¡Campaña anterior completada! Se ha generado un nuevo archivo de reportes para reiniciar el ciclo.', parent=root)
            except Exception as error:
                messagebox.showerror('Campaña', str(error), parent=root)
                return
        _persistencia.guardar_config(asunto, cuerpo, asunto_gestion, tam_lote=f_idx - i_idx + 1 if f_idx >= i_idx and (not reintento_preparado) else None, dry_run=dry_run_var.get(), ruta_pdf=ruta_pdf_var.get(), huella_campana=huella_actual if not dry_run_var.get() else None)
        if not dry_run_var.get():
            huella_campana_guardada = huella_actual
        args = (u_crm, p_crm, i_idx, f_idx, ruta_pdf_var.get(), headless_var.get(), asunto, cuerpo, asunto_gestion, dry_run_var.get(), set(reintento_confirmado_id or ()), set(solo_gestion_id or ()), log_destino, set(solo_ids))
        reintento_confirmado_id, solo_gestion_id, log_destino = (None, None, None)
        solo_ids = set()
        reintento_preparado = False
        _eventos.DETENER.clear()
        def abrir_progreso():
            root.gestor_progreso = _progreso.VentanaProgreso(root, args)
        root.after(50, abrir_progreso)

    def confirmar_cierre_sesion_gmail():
        messagebox.showinfo('Demostración local', 'No hay ninguna sesión de Gmail abierta. No se borran perfiles ni se usan credenciales.', parent=root)
    pie.columnconfigure(0, weight=3)
    pie.columnconfigure(1, weight=1)
    ttk.Button(pie, text='🚀 Iniciar simulación', style='Accent.TButton', command=al_presionar_iniciar).grid(row=0, column=0, sticky='ew', padx=(0, 8))
    ttk.Button(pie, text='Sin sesión de Gmail', command=confirmar_cierre_sesion_gmail).grid(row=0, column=1, sticky='ew')
    controles = {'root': root, 'inicio': entry_inicio, 'fin': entry_fin, 'asunto': asunto_var,
                 'mensaje': txt_cuerpo, 'pdf': ruta_pdf_var, 'prueba': dry_run_var,
                 'usuario': entry_user_crm, 'password': entry_pass_crm,
                 'simular': al_presionar_iniciar, 'vista_previa': vista_previa,
                 'sincronizar': iniciar_sincronizacion, 'base': lbl_base}
    root.gestor_controles = controles
    if ejecutar_bucle:
        root.mainloop()
    return controles

def vista_previa_ventana():
    raise RuntimeError('Integración real deshabilitada en la versión de portafolio. Usa el modo demostración.')
    root = ctk.CTk()
    _tema.aplicar_tema(root)

    class Demo(_progreso.VentanaProgreso):

        def _trabajo(self, *args):
            ejemplos = ['🖥️ Sistema detectado: macOS', '-> Entrando al Manager...', '   ✓ Gmail listo.', '   ⚠️ Aviso de ejemplo', '   ❌ Error de ejemplo', '   ⚙️ [CDP foco] Mensaje de depuración']
            for i in range(60):
                _eventos.COLA.put(('log', f'[{i + 1}/60] {ejemplos[i % len(ejemplos)]}'))
                time.sleep(0.15)
            _eventos.COLA.put(('fin',))
    Demo(root, ())
    root.mainloop()

# Decisiones de separación

## Dos recorridos explícitos

`main.py` inicia únicamente la demo. `demostracion.py` reutiliza las funciones de limpieza de contactos y plantillas del programa original. `interfaz_demo.py` abre el formulario original de `formulario.py`. Los campos de cuenta conservan su lugar en el diseño, pero muestran valores ficticios y están deshabilitados. `adaptadores_demo.py` carga los ejemplos locales y conecta la ventana original de progreso a la simulación. No se consulta el llavero ni se abren navegadores.

La automatización conectada a servicios reales permanece distribuida en módulos, con errores explícitos al intentar activar sus puntos de entrada. No hay una opción de terminal que la habilite. Se conserva para que sea posible revisar el trabajo anterior sin confundirlo con una integración funcional genérica.

## Dependencias

Los módulos usan importaciones explícitas. No se ejecuta el archivo monolítico mediante `exec` ni se comparte un diccionario global para simular módulos. `eventos.py` contiene las colas y señales compartidas que antes eran globales; los demás componentes acceden a ese estado mediante el módulo correspondiente.

Las rutas de datos están centralizadas en `configuracion.py`. Importar el paquete no crea la configuración de la aplicación original. Las dependencias de navegador, llavero e interfaz histórica se separan de los requisitos mínimos de la demo.

## Cambios intencionales

- No se copiaron archivos de configuración, contactos, logs, reportes, perfiles, logos ni ejecutables originales.
- Se retiraron nombres y destinos de la organización original del código de la copia.
- Se reemplazaron los puntos de entrada reales por errores explícitos antes de iniciar las operaciones.
- La primera versión usó una interfaz simplificada. A petición del usuario, se restauraron el formulario, el tema y el progreso originales con adaptadores de demostración e identidad genérica.
- Se añadieron comprobaciones de equivalencia para una parte de las funciones puras y pruebas del recorrido de demostración.

Los 120 elementos registrados son funciones y clases de nivel superior. Sus métodos y funciones anidadas se conservan dentro de cada definición; no se cuentan como elementos nuevos. La separación no acredita por sí sola una equivalencia total con el programa original ni compatibilidad de sus integraciones.

## Restauración del diseño original

El formulario conserva su estructura de tarjetas, rango de contactos, mensaje, adjuntos y pie de acciones. «Cargar base de ejemplo» sustituye la sincronización web. Los campos de usuario, contraseña, ejecutivo y recuerdo de credenciales están bloqueados. El modo prueba está activo y no se puede desmarcar desde la ventana. La simulación tampoco realiza envíos si alguien llama al adaptador con dry_run=False.

`progreso.py` usa exclusivamente `adaptadores_demo.ejecutar_campana`. Su ficha está rotulada «Simulados» y genera un reporte JSON en datos/reportes_demo. No importa los módulos de automatización real. Los logos de la organización original siguen excluidos.

`lanzar_gui` admite ahora root y ejecutar_bucle como argumentos opcionales para construir y comprobar la ventana sin bloquear las pruebas en mainloop. La llamada sin argumentos sigue abriendo la aplicación.

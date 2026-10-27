# Decisiones de separación

## Dos recorridos explícitos

`main.py` inicia únicamente la demo. `demostracion.py` reutiliza las funciones de limpieza de contactos y plantillas del programa original. `interfaz_demo.py` presenta ese recorrido sin formularios de credenciales ni navegadores.

La automatización conectada a servicios reales permanece distribuida en módulos, con errores explícitos al intentar activar sus puntos de entrada. No hay una opción de terminal que la habilite. Se conserva para que sea posible revisar el trabajo anterior sin confundirlo con una integración funcional genérica.

## Dependencias

Los módulos usan importaciones explícitas. No se ejecuta el archivo monolítico mediante `exec` ni se comparte un diccionario global para simular módulos. `eventos.py` contiene las colas y señales compartidas que antes eran globales; los demás componentes acceden a ese estado mediante el módulo correspondiente.

Las rutas de datos están centralizadas en `configuracion.py`. Importar el paquete no crea la configuración de la aplicación original. Las dependencias de navegador, llavero e interfaz histórica se separan de los requisitos mínimos de la demo.

## Cambios intencionales

- No se copiaron archivos de configuración, contactos, logs, reportes, perfiles, logos ni ejecutables originales.
- Se retiraron nombres y destinos de la organización original del código de la copia.
- Se reemplazaron los puntos de entrada reales por errores explícitos antes de iniciar las operaciones.
- Se creó una interfaz de demostración con contactos ficticios.
- Se añadieron comprobaciones de equivalencia para una parte de las funciones puras y pruebas del recorrido de demostración.

Los 120 elementos registrados son funciones y clases de nivel superior. Sus métodos y funciones anidadas se conservan dentro de cada definición; no se cuentan como elementos nuevos. La separación no acredita por sí sola una equivalencia total con el programa original ni compatibilidad de sus integraciones.

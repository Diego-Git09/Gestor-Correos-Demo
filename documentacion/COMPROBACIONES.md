# Comprobaciones de la copia de portafolio

Fecha: 27 de octubre de 2026.

## Separación y original

- El SHA256 del archivo original coincide con el registrado al comenzar: no se modificó.
- Las 120 funciones y clases de nivel superior tienen correspondencia en 21 módulos.
- Los parámetros se conservaron. Dos valores predeterminados ahora referencian sus constantes mediante el módulo de configuración o tema correspondiente.
- Los métodos y funciones anidadas permanecen dentro de sus clases o funciones.
- Los 28 archivos Python actuales no presentan errores de sintaxis. Se comprobaron las importaciones de todos los módulos con las dependencias de desarrollo.

## Funcionamiento comprobado

- 12 pruebas aprobadas en el entorno de desarrollo, incluidas 2 pruebas con ventana Tk real.
- Una de esas pruebas contiene 29 casos de equivalencia de funciones puras, con resultados de referencia obtenidos del original usando datos ficticios. No se suman como 29 pruebas independientes.
- Se probaron limpieza y deduplicación de contactos, plantillas, correos no válidos, variables desconocidas, lotes vacíos y exportación sin sobrescritura.
- Se creó un PDF ficticio, se validó como adjunto y se comprobó que su contenido no cambia. Se rechazaron un PDF falso y uno cifrado.
- La simulación de los 3 contactos de ejemplo produce 2 resultados simulados, 1 omitido y 0 envíos reales.
- Se comprobaron cinco puntos de entrada reales bloqueados: creación de navegador, cierre de sesión, recuperación de credenciales, acceso al CRM y registro de gestión. Los bloqueos se verificaron con las conexiones de red sustituidas por errores de prueba.

## Instalación mínima

Se creó un segundo entorno virtual nuevo y se instaló únicamente pypdf 6.21.3. La demo de terminal funcionó y `pip check` no encontró incompatibilidades. Sus pruebas produjeron 9 aprobadas y 3 omisiones explícitas: dos necesitan sesión gráfica y una requiere las dependencias de los módulos históricos. Las dos de ventana se ejecutaron después con ese mismo entorno mínimo y pasaron.

No se instaló nada en el Python habitual. Las fuentes que CustomTkinter prepara al importarse se mantuvieron dentro de un hogar temporal de pruebas. No se usaron cuentas reales, Selenium contra servicios reales, correos de clientes, perfiles originales ni credenciales.

## Revisión de datos

No se copiaron los JSON de configuración y contactos, CSV de envíos, registros, logos, iconos ni el ejecutable original. La búsqueda estática final no encontró nombres o dominios de la organización original ni formatos comunes de claves. Esto no garantiza detectar cualquier dato sensible; es una revisión estática con alcance limitado.

Las direcciones incluidas como contactos usan `example.invalid`. Las referencias genéricas de Gmail permanecen en módulos históricos bloqueados y no forman parte del recorrido de demostración.

## Límites

El recorrido real de CRM y correo cambió intencionalmente: sus puntos de entrada están deshabilitados. No se acredita equivalencia de toda la aplicación original, ejecución real de campañas, reconexión de navegadores ni compatibilidad de las integraciones con las versiones nuevas de sus bibliotecas.

La nueva interfaz es una demostración propia; no se presenta como una réplica exacta del formulario original. Las funciones originales de interfaz permanecen separadas para revisión. Las pruebas se hicieron en este equipo Linux con Python 3.14.4, no en Windows ni macOS.

No se creó un repositorio remoto, no se hicieron commits ni se publicó código. La selección final de archivos, la licencia y la subida manual por el usuario siguen pendientes.

"""Inicio único del portafolio; no ofrece un modo de envío real."""
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description='Gestor de correos: demostración local sin envíos.')
    parser.add_argument('--demo-cli', action='store_true', help='Simular el lote ficticio sin abrir ventanas.')
    parser.add_argument('--reporte', help='Guardar un reporte JSON nuevo al usar --demo-cli.')
    args = parser.parse_args()
    if args.reporte and not args.demo_cli:
        parser.error('--reporte requiere --demo-cli')
    if args.demo_cli:
        from gestor_correos.demostracion import cargar_ejemplos, preparar_demostracion, resumen, exportar_reporte
        resultados = preparar_demostracion(cargar_ejemplos())
        if args.reporte:
            exportar_reporte(args.reporte, resultados)
        print(json.dumps(resumen(resultados), ensure_ascii=False))
    else:
        from gestor_correos.interfaz_demo import iniciar
        iniciar()


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # if sys.platform == 'win32':
    #    sys.stdout.reconfigure(encoding='utf-8')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dahell_backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    try:
        execute_from_command_line(sys.argv)
    except UnicodeDecodeError as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        print(f"CRITICO: UNICODE DECODE ERROR CAPTURADO", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        try:
            # Imprimir contexto hex
            obj = e.object
            start = max(0, e.start - 20)
            end = min(len(obj), e.end + 20)
            print(f"Contexto (Bytes): {obj[start:end]}", file=sys.stderr)
            print(f"Contexto (Hex): {obj[start:end].hex()}", file=sys.stderr)
            # Intentar decodificar como latin-1 para leer texto
            print(f"Contexto (Latin-1): {obj[start:end].decode('latin-1', errors='replace')}", file=sys.stderr)
        except:
            print("No se pudo extraer contexto", file=sys.stderr)
        sys.exit(1)
    except Exception:
        import traceback
        sys.stderr.buffer.write(traceback.format_exc().encode('utf-8', 'replace'))
        sys.exit(1)


if __name__ == '__main__':
    main()

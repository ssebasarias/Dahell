from django.core.management.base import BaseCommand
import traceback
from django.db import connection

class Command(BaseCommand):
    help = 'Debug Connection Encoding'

    def handle(self, *args, **options):
        with open('debug_conn.log', 'w', encoding='utf-8') as f:
            try:
                print("Checking connection...", file=f)
                cursor = connection.cursor()
                # Force encoding check
                print(f"Connection encoding: {connection.connection.encoding}", file=f)
                
                # Force set to LATIN1 if it's UTF8
                if connection.connection.encoding != 'LATIN1':
                    print("Forcing LATIN1...", file=f)
                    connection.connection.set_client_encoding('LATIN1')
                    print(f"New encoding: {connection.connection.encoding}", file=f)
                
                from core.models import Product
                p = Product.objects.first()
                if p:
                    print(f"Fetched title: {repr(p.title)}", file=f)

            except Exception as e:
                print("CRITICAL ERROR:", file=f)
                traceback.print_exc(file=f)

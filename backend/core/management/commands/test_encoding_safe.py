from django.core.management.base import BaseCommand
import psycopg2
from django.conf import settings

class Command(BaseCommand):
    help = 'Test DB Encoding Safe'

    def handle(self, *args, **options):
        db_conf = settings.DATABASES['default']
        print(f"Checking Settings Encoding: {db_conf['OPTIONS'].get('client_encoding')}")
        
        try:
            print("\n--- TEST: LATIN1 fetching ---")
            conn = psycopg2.connect(
                dbname=db_conf['NAME'],
                user=db_conf['USER'],
                password=db_conf['PASSWORD'],
                host=db_conf['HOST'],
                port=db_conf['PORT'],
                client_encoding='LATIN1'
            )
            cur = conn.cursor()
            cur.execute("SELECT title FROM products LIMIT 5;")
            print("Query executed. Fetching...")
            rows = cur.fetchall()
            print("Fetched.")
            for r in rows:
                # Use repr to avoid print encoding errors
                print(f"Row: {repr(r)}")
            conn.close()
            print("SUCCESS")
            
        except Exception as e:
            print(f"FAILED: {e}")

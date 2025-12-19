from django.core.management.base import BaseCommand
import psycopg2
from django.conf import settings

class Command(BaseCommand):
    help = 'Test DB Encoding'

    def handle(self, *args, **options):
        db_conf = settings.DATABASES['default']
        print(f"Connecting to {db_conf['NAME']} as {db_conf['USER']}...")
        
        try:
            # Test 1: Standard Connection (UTF8)
            print("\n--- TEST 1: UTF8 (Default) ---")
            conn = psycopg2.connect(
                dbname=db_conf['NAME'],
                user=db_conf['USER'],
                password=db_conf['PASSWORD'],
                host=db_conf['HOST'],
                port=db_conf['PORT'],
                client_encoding='UTF8'
            )
            cur = conn.cursor()
            cur.execute("SELECT title FROM products LIMIT 5;")
            rows = cur.fetchall()
            for r in rows:
                print(f"Row: {r}")
            conn.close()
            print("UTF8 SUCCESS")

        except Exception as e:
            print(f"UTF8 FAILED: {e}")

        try:
            # Test 2: LATIN1
            print("\n--- TEST 2: LATIN1 ---")
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
            rows = cur.fetchall()
            for r in rows:
                print(f"Row: {r}")
            conn.close()
            print("LATIN1 SUCCESS")
            
        except Exception as e:
            print(f"LATIN1 FAILED: {e}")

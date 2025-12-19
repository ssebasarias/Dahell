import psycopg2
import sys

print(f"Testing connection to 127.0.0.1:5433 with utf8 client_encoding...")
try:
    conn = psycopg2.connect(
        dbname='dahell_db',
        user='dahell_admin',
        password='secure_password_123',
        host='127.0.0.1',
        port='5433',
        options='-c client_encoding=utf8'
    )
    print("✅ Connected successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Failed: {e}")

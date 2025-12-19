import os
import sys
import django

# Setup path
sys.path.append(r"c:\Users\guerr\Documents\AnalisisDeDatos\Dahell\backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dahell_backend.settings')

try:
    django.setup()
    from django.conf import settings
    db = settings.DATABASES['default']
    print("--- DJANGO CONFIG ---")
    print(f"HOST: '{db['HOST']}'")
    print(f"PORT: '{db['PORT']}'")
    print(f"NAME: '{db['NAME']}'")
    print(f"USER: '{db['USER']}'")
    print(f"PASS: '{db['PASSWORD']}'")
    
    # Test connection via Django
    from django.db import connection
    try:
        connection.ensure_connection()
        print("✅ Django Connection SUCCESS")
    except Exception as e:
        print(f"❌ Django Connection FAILED: {e}")

except Exception as e:
    print(f"❌ Setup Failed: {e}")

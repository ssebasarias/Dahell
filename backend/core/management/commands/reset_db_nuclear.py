from django.core.management.base import BaseCommand
import sys

class Command(BaseCommand):
    help = 'Aggressively clean DB'

    def handle(self, *args, **options):
        from django.db import connection
        with connection.cursor() as cursor:
            # Drop tables to force clean slate (User data is in raw_data/ anyway if needed)
            # This is extreme but will fix the encoding mismatch 100%
            cursor.execute("DROP SCHEMA public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            print("SCHEMA CLEARED")

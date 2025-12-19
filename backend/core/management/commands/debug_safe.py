from django.core.management.base import BaseCommand
import sys

class Command(BaseCommand):
    help = 'Debug Connection Safe'

    def handle(self, *args, **options):
        with open('debug_safe.log', 'w', encoding='utf-8') as f:
            try:
                from django.db import connection
                print("Attempting connection...", file=f)
                c = connection.cursor()
                print("Cursor obtained.", file=f)
            except Exception as e:
                print("ERROR CAUGHT", file=f)
                # Print REPR to see the raw bytes without decoding
                print(f"Exception repr: {repr(e)}", file=f)

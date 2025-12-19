try:
    import psycopg2
    print("✅ psycopg2 importado con éxito")
    conn = psycopg2.connect(datetime=None) # Intencionalmente mal para ver si llega aqui
except Exception as e:
    print(f"❌ Error: {e}")

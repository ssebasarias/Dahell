import os
import glob

def fix_file_encoding(start_path):
    count = 0
    # Recorrer recursivamente
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    # Intento 1: Leer como UTF-8 (Si pasa, ya es UTF-8, no tocar)
                    with open(path, 'r', encoding='utf-8') as f:
                        f.read()
                    # print(f"✅ {file} ya es UTF-8")
                except UnicodeDecodeError:
                    # Intento 2: Leer como Latin-1 y Guardar como UTF-8
                    print(f"⚠️  REPARANDO: {file} (Era Latin-1)")
                    try:
                        with open(path, 'r', encoding='latin-1') as f:
                            content = f.read()
                        
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        count += 1
                    except Exception as e:
                        print(f"❌ Error salvando {file}: {e}")

    print(f"✨ Total archivos reparados: {count}")

if __name__ == "__main__":
    base_dir = r"c:\Users\guerr\Documents\AnalisisDeDatos\Dahell\backend"
    fix_file_encoding(base_dir)

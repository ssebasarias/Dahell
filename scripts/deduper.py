import pandas as pd, requests, io, os, imagehash, traceback
from PIL import Image
from rapidfuzz.fuzz import token_set_ratio
from rapidfuzz.distance.Levenshtein import normalized_similarity

CSV = "catalogo_dropi.csv"
IMG_CACHE = "thumbs/"          # carpeta local

SIM_THRESHOLD = 80             # ≥80 ⇒ nombres muy parecidos
HASH_THRESHOLD = 6             # Hamming distance ≤6 ⇒ misma imagen

# 1) lee CSV
df = pd.read_csv(CSV)

# 2) baja miniaturas y calcula phash
os.makedirs(IMG_CACHE, exist_ok=True)
hashes = {}
def get_hash(url):
    if not isinstance(url, str) or not url:
        return None
    fname = os.path.join(IMG_CACHE, url.split("/")[-1])
    if not os.path.exists(fname):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            Image.open(io.BytesIO(r.content)).save(fname)
        except Exception:
            traceback.print_exc()
            return None
    try:
        return imagehash.phash(Image.open(fname))
    except Exception:
        return None

df["phash"] = df["Imagen"].apply(get_hash)

# 3) clustering ingenuo (O(n²) → bien para unos miles de filas)
clusters = {}
cluster_id = 0
for i, row_i in df.iterrows():
    if i in clusters:
        continue
    clusters[i] = cluster_id
    for j, row_j in df.loc[i+1:].iterrows():
        if j in clusters:
            continue
        # criterio imagen
        same_pic = (row_i["phash"] and row_j["phash"] 
                    and row_i["phash"] - row_j["phash"] <= HASH_THRESHOLD)
        # criterio nombre
        sim = token_set_ratio(str(row_i["Nombre"]), str(row_j["Nombre"]))
        same_name = sim >= SIM_THRESHOLD
        if same_pic or same_name:
            clusters[j] = cluster_id
    cluster_id += 1

df["cluster_id"] = df.index.map(clusters)

# 4) resumen
summary = (
    df.groupby("cluster_id")
      .agg(total_vendedores=("Proveedor", "nunique"),
           ejemplos=("Nombre", lambda x: list(x)[:3]),
           precio_min=("Precio", "min"),
           precio_max=("Precio", "max"))
      .reset_index()
      .sort_values("total_vendedores", ascending=False)
)

print(summary.head(10))

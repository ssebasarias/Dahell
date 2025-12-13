-- products_raw quick inspection
SELECT COUNT(*) AS total_rows FROM products_raw;

-- How many are missing pHash?
SELECT COUNT(*) AS missing_phash FROM products_raw WHERE phash IS NULL;

-- How many are missing image_url?
SELECT COUNT(*) AS missing_image_url FROM products_raw WHERE image_url IS NULL OR image_url = '';

-- Recent rows
SELECT id, sku, name, image_url, phash, capture_ts
FROM products_raw
ORDER BY capture_ts DESC NULLS LAST
LIMIT 50;

-- Distribution by supplier
SELECT COALESCE(user_id, -1) AS user_id, COALESCE(user_name, '(null)') AS user_name, COUNT(*) AS n
FROM products_raw
GROUP BY ALL
ORDER BY n DESC;

-- Rows eligible to compute pHash now
SELECT id, image_url
FROM products_raw
WHERE phash IS NULL AND image_url IS NOT NULL AND image_url <> ''
LIMIT 200;

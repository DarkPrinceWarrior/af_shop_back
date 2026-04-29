# Seed Data

The backend can start with custom catalog data from JSON.

Default lookup path:

```text
seed/shop_seed.json
```

To start from the template:

```bash
cp seed/shop_seed.example.json seed/shop_seed.json
```

On Windows PowerShell:

```powershell
Copy-Item seed/shop_seed.example.json seed/shop_seed.json
```

Then edit `seed/shop_seed.json`.

## Format

Root keys:

- `categories`
- `delivery_places`
- `products`

Products use `category_name_en` to link to a category by exact English name.

Money values should be strings, for example:

```json
"price_afn": "120.00"
```

Product image paths and delivery-place image paths are stored as URLs, usually under `/media/...`.
The seed loader does not copy images. Upload or place media separately, then reference the final path in JSON.

## Startup Behavior

On startup `app/initial_data.py` checks `SHOP_SEED_FILE`.
If it is empty, it tries `seed/shop_seed.json`.

If the JSON file exists, it seeds from that file.
If the file does not exist, it falls back to built-in demo data.

The seed is idempotent per table:

- existing categories are not recreated;
- existing delivery places are not recreated;
- existing products are not recreated.

For local development, to reseed from scratch, remove the Docker volumes and start again:

```bash
docker compose down -v
docker compose up --build -d
```

Do not run `down -v` on production unless you intentionally want to delete the database volume.

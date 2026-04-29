import json

from app.initial_data import _load_external_seed


def test_load_external_seed_from_env_path(monkeypatch, tmp_path) -> None:
    seed_file = tmp_path / "shop_seed.json"
    seed_file.write_text(
        json.dumps({"categories": [], "delivery_places": [], "products": []}),
        encoding="utf-8",
    )
    monkeypatch.setenv("SHOP_SEED_FILE", str(seed_file))

    seed_data = _load_external_seed()

    assert seed_data == {"categories": [], "delivery_places": [], "products": []}


def test_load_external_seed_returns_none_for_missing_file(monkeypatch) -> None:
    monkeypatch.setenv("SHOP_SEED_FILE", "missing-shop-seed.json")

    assert _load_external_seed() is None

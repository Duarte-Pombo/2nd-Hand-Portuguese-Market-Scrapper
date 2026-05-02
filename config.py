import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".tech_deal_finder" / "config.json"

DEFAULT_CONFIG: dict = {
    "fb_email":             "",
    "fb_password":          "",
    "max_results_per_site": 30,
    "headless_browser":     True,
    "weights": {
        "price":     0.50,
        "condition": 0.30,
        "location":  0.20,
    },
    "enabled_sites": {
        "olx":        True,
        "custojusto": True,
        "ebay":       True,
        "backmarket": True,
        "facebook":   False,
    },
    "last_query":     "",
    "last_category":  "All PC & Laptops",
    "max_price":      0,
    "min_price":      0,
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config() -> dict:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                return _deep_merge(DEFAULT_CONFIG, json.load(f))
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

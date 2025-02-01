# agaip/config.py
import yaml
import os

def load_config(config_path: str = "config.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config dosyası bulunamadı: {config_path}")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config

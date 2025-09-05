# Unified config loader for OMOP Agent
import yaml
import os

def load_config(config_path="config.yaml"):
    # Try to load config from the given path or current working directory
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), "..", config_path)
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config

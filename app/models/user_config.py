import json
import base64

def encode_config(config_dict: dict) -> str:
    """Encode dict config to base64 string"""
    json_str = json.dumps(config_dict)
    return base64.urlsafe_b64encode(json_str.encode()).decode().rstrip("=")

def decode_config(config_str: str) -> dict:
    """Decode base64 string to dict config"""
    try:
        padding = '=' * (-len(config_str) % 4)
        json_str = base64.urlsafe_b64decode(config_str + padding).decode()
        return json.loads(json_str)
    except Exception:
        return {}
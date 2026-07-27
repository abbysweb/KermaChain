import json


def canonicalize(obj) -> bytes:
    return json.dumps(obj, separators=(',', ':'), sort_keys=True).encode('utf-8')

import hashlib
import json


def elem_hash(elem: dict) -> str:
    block_string = json.dumps(elem, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()

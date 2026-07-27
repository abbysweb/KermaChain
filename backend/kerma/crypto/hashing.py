import hashlib
from kerma.crypto.jcs import canonicalize


def get_objid(obj_dict: dict) -> str:
    return hashlib.blake2s(canonicalize(obj_dict)).hexdigest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

import copy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from kerma.crypto.jcs import canonicalize


def verify_signature(tx_dict: dict, sig_hex: str, pubkey_hex: str) -> bool:
    tx_local = copy.deepcopy(tx_dict)
    for inp in tx_local["inputs"]:
        inp["sig"] = None
    pubkey_obj = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex))
    sig_bytes = bytes.fromhex(sig_hex)
    try:
        pubkey_obj.verify(sig_bytes, canonicalize(tx_local))
        return True
    except InvalidSignature:
        return False

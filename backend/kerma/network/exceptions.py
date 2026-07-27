from abc import ABC


class NodeException(ABC, Exception):
    def __init__(self, message, error_name) -> None:
        self.error_name = error_name
        self.message = message
        super().__init__(self.message, self.error_name)


class FaultyNodeException(NodeException):
    def __init__(self, message, error_name) -> None:
        self.error_name = error_name
        self.message = message
        super().__init__(self.message, self.error_name)


class NonfaultyNodeException(NodeException):
    def __init__(self, message, error_name) -> None:
        self.error_name = error_name
        self.message = message
        super().__init__(self.message, self.error_name)


class ErrorInvalidFormat(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_FORMAT")


class ErrorInvalidHandshake(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_HANDSHAKE")


class ErrorInvalidTxSignature(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_TX_SIGNATURE")


class ErrorInvalidTxConservation(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_TX_CONSERVATION")


class ErrorInvalidTxOutpoint(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_TX_OUTPOINT")


class ErrorInvalidBlockTimestamp(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_BLOCK_TIMESTAMP")


class ErrorInvalidGenesis(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_GENESIS")


class ErrorInvalidBlockPOW(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_BLOCK_POW")


class ErrorInvalidBlockCoinbase(FaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "INVALID_BLOCK_COINBASE")


class ErrorUnknownObject(NonfaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "UNKNOWN_OBJECT")


class ErrorUnfindableObject(NonfaultyNodeException):
    def __init__(self, message) -> None:
        super().__init__(message, "UNFINDABLE_OBJECT")


class NeedMoreObjects(NonfaultyNodeException):
    def __init__(self, message, missingobjids) -> None:
        self.missingobjids = missingobjids
        super().__init__(message, "---")

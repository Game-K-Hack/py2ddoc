"""Exceptions for the py2ddoc library."""


class TwoDBarcodeError(Exception):
    """Base exception for all 2D-Doc errors."""


class ParseError(TwoDBarcodeError):
    """Raised when the barcode content cannot be parsed."""


class SignatureError(TwoDBarcodeError):
    """Raised when signature verification fails."""


class CertificateNotFoundError(TwoDBarcodeError):
    """Raised when no certificate matches the CA/cert ID in the barcode."""

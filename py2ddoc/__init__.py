"""
py2ddoc — Decode and verify French ANTS 2D-Doc barcodes.

Quickstart (TSL bundlé, aucun fichier externe nécessaire)::

    from py2ddoc import TwoDDoc

    doc = TwoDDoc.from_string(barcode_content)   # vérifie avec le TSL intégré
    print(doc)               # résumé lisible
    print(doc.is_authentic)  # True si la signature est valide
    print(doc.named_fields)  # champs avec noms explicites

Ou avec un TSL externe (avancé)::

    from py2ddoc import TwoDDoc, TrustStore

    store = TrustStore.from_tsl("/chemin/vers/tsl_signed.xml")
    doc = TwoDDoc.from_string(barcode_content, trust_store=store)
"""

from .doc import Doc2D, TwoDDoc
from .exceptions import (
    CertificateNotFoundError,
    ParseError,
    SignatureError,
    TwoDBarcodeError,
)
from .parser import parse, ParsedDoc
from .tsl import CertEntry, TrustStore

__all__ = [
    "TwoDDoc",
    "Doc2D",
    "TrustStore",
    "CertEntry",
    "ParsedDoc",
    "parse",
    "TwoDBarcodeError",
    "ParseError",
    "SignatureError",
    "CertificateNotFoundError",
]

__version__ = "0.1.0"
__author__ = "py2ddoc contributors"

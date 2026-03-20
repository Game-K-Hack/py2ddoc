"""
Signature verification for 2D-Doc barcodes.

Supported signing algorithms:
- ECDSA with P-256 (secp256r1) and SHA-256  → used in v3/v4 (most common)
- ECDSA with P-384 (secp384r1) and SHA-384  → some v4 certificates
- RSA-PKCS1v15 with SHA-256                 → used in v2 and some v3

The signed data is the raw message (header + data fields, everything
before \\x1f), encoded as ISO-8859-1.

The signature is the raw concatenation of (r, s) in big-endian byte
order, base-32 encoded without padding.
"""

from __future__ import annotations

from typing import List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePublicKey,
    SECP256R1,
    SECP384R1,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from .exceptions import CertificateNotFoundError, SignatureError
from .parser import ParsedDoc
from .tsl import CertEntry, TrustStore


def _hash_for_curve(curve) -> hashes.HashAlgorithm:
    if isinstance(curve, SECP384R1):
        return hashes.SHA384()
    return hashes.SHA256()


def _verify_one(public_key, message_bytes: bytes, sig_bytes: bytes) -> bool:
    """
    Try to verify the signature with the given public key.

    Returns True on success, False on invalid signature.
    Raises ValueError / TypeError on algorithm mismatch.
    """
    if isinstance(public_key, EllipticCurvePublicKey):
        # sig_bytes = r || s (each curve_size bytes, big-endian)
        key_size = (public_key.key_size + 7) // 8
        if len(sig_bytes) != 2 * key_size:
            return False
        r = int.from_bytes(sig_bytes[:key_size], "big")
        s = int.from_bytes(sig_bytes[key_size:], "big")
        der_sig = encode_dss_signature(r, s)
        hash_alg = _hash_for_curve(public_key.curve)
        try:
            public_key.verify(der_sig, message_bytes, ec.ECDSA(hash_alg))
            return True
        except InvalidSignature:
            return False

    if isinstance(public_key, RSAPublicKey):
        try:
            public_key.verify(
                sig_bytes,
                message_bytes,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False

    raise TypeError(f"Unsupported public key type: {type(public_key)}")


def verify(doc: ParsedDoc, trust_store: TrustStore) -> CertEntry:
    """
    Verify the digital signature of a parsed 2D-Doc.

    Looks up all certificates matching ``doc.ca_id`` in *trust_store* and
    tries each one until the signature verifies.

    Args:
        doc: A :class:`~py2ddoc.parser.ParsedDoc` returned by :func:`~py2ddoc.parser.parse`.
        trust_store: A :class:`~py2ddoc.tsl.TrustStore` containing the CA certificates.

    Returns:
        The :class:`~py2ddoc.tsl.CertEntry` that successfully verified the signature.

    Raises:
        CertificateNotFoundError: If no certificate for ``doc.ca_id`` is in the store.
        SignatureError: If all matching certificates fail to verify the signature.
    """
    candidates: List[CertEntry] = trust_store.get(doc.ca_id)

    if not candidates:
        # Fallback: try all certificates (useful when CA ID mapping is uncertain)
        candidates = trust_store.all_entries()

    if not candidates:
        raise CertificateNotFoundError(
            f"No certificate found for CA ID '{doc.ca_id}' in the trust store. "
            f"Available CA IDs: {trust_store.ca_ids()}"
        )

    # The signed data is the message encoded in Latin-1 (ISO-8859-1)
    try:
        message_bytes = doc.message.encode("latin-1")
    except UnicodeEncodeError:
        message_bytes = doc.message.encode("utf-8")

    sig_bytes = doc.signature_bytes

    errors: List[str] = []
    for entry in candidates:
        try:
            ok = _verify_one(entry.public_key, message_bytes, sig_bytes)
            if ok:
                return entry
            errors.append(f"{entry!r}: invalid signature")
        except Exception as exc:
            errors.append(f"{entry!r}: {exc}")

    raise SignatureError(
        f"Signature verification failed for CA '{doc.ca_id}'. "
        f"Tried {len(candidates)} certificate(s).\n"
        + "\n".join(f"  - {e}" for e in errors)
    )

"""
TSL (Trust Service Status List) XML parser.

Loads X.509 certificates from an ANTS 2D-Doc TSL file and indexes them
by CA identifier (TSP trade name, e.g. "FR01", "FR03", ...).

The official ANTS TSL is bundled in this package and can be loaded via
:meth:`TrustStore.from_bundled_tsl`.
"""

from __future__ import annotations

import base64
import importlib.resources
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

TSL_NS = {
    "tsl": "http://uri.etsi.org/02231/v2#",
    "ds":  "http://www.w3.org/2000/09/xmldsig#",
}


class CertEntry:
    """A certificate loaded from the TSL."""

    def __init__(self, ca_id: str, cert: x509.Certificate):
        self.ca_id = ca_id
        self.cert = cert

    @property
    def public_key(self):
        return self.cert.public_key()

    @property
    def subject(self) -> str:
        return self.cert.subject.rfc4514_string()

    @property
    def not_valid_before(self):
        return self.cert.not_valid_before_utc

    @property
    def not_valid_after(self):
        return self.cert.not_valid_after_utc

    @property
    def key_type(self) -> str:
        pk = self.public_key
        if isinstance(pk, EllipticCurvePublicKey):
            return f"EC/{pk.curve.name}"
        if isinstance(pk, RSAPublicKey):
            return f"RSA/{pk.key_size}"
        return type(pk).__name__

    def __repr__(self) -> str:
        return f"<CertEntry ca_id={self.ca_id!r} key={self.key_type} subject={self.subject!r}>"


_DEFAULT_STORE: Optional["TrustStore"] = None


class TrustStore:
    """
    Collection of certificates indexed by CA ID.

    Usage::

        store = TrustStore.from_bundled_tsl()
        certs = store.get("FR01")
    """

    def __init__(self):
        self._certs: Dict[str, List[CertEntry]] = {}

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    @classmethod
    def from_tsl(cls, path: str | Path) -> "TrustStore":
        """Load all certificates from an ANTS TSL XML file."""
        store = cls()
        tree = ET.parse(str(path))
        root = tree.getroot()

        for tsp in root.findall(".//tsl:TrustServiceProvider", TSL_NS):
            # Determine CA ID from TSP trade name (e.g. "FR01", "FR03")
            trade_name_el = tsp.find(
                ".//tsl:TSPTradeName/tsl:Name", TSL_NS
            )
            ca_id = trade_name_el.text.strip() if trade_name_el is not None else None
            if not ca_id:
                continue

            # Load all X.509 certificates in this TSP's services
            for cert_el in tsp.findall(
                ".//tsl:ServiceDigitalIdentity/tsl:DigitalId/tsl:X509Certificate",
                TSL_NS,
            ):
                if not cert_el.text:
                    continue
                try:
                    der = base64.b64decode(cert_el.text.strip())
                    cert = x509.load_der_x509_certificate(der)
                    entry = CertEntry(ca_id=ca_id, cert=cert)
                    store._certs.setdefault(ca_id, []).append(entry)
                except Exception:
                    continue  # skip malformed certificate

        return store

    @classmethod
    def from_der(cls, ca_id: str, der: bytes) -> "TrustStore":
        """Build a TrustStore from a single DER-encoded certificate."""
        store = cls()
        cert = x509.load_der_x509_certificate(der)
        store._certs[ca_id] = [CertEntry(ca_id=ca_id, cert=cert)]
        return store

    @classmethod
    def from_pem(cls, ca_id: str, pem: bytes | str) -> "TrustStore":
        """Build a TrustStore from a single PEM-encoded certificate."""
        store = cls()
        if isinstance(pem, str):
            pem = pem.encode()
        cert = x509.load_pem_x509_certificate(pem)
        store._certs[ca_id] = [CertEntry(ca_id=ca_id, cert=cert)]
        return store

    @classmethod
    def from_bundled_tsl(cls) -> "TrustStore":
        """
        Load the ANTS TSL that is bundled with this package.

        This is the official list published by the French government at
        https://pub.ants.gouv.fr/2D-DOC/V1/PRD/01_TSL/tsl_signed.xml
        and covers all authorised 2D-Doc certification authorities.

        Returns:
            A :class:`TrustStore` pre-loaded with all ANTS CA certificates.
        """
        pkg = importlib.resources.files(__package__)
        tsl_bytes = (pkg / "tsl_signed.xml").read_bytes()
        # Parse from the in-memory bytes to avoid temp-file issues on all platforms
        root = ET.fromstring(tsl_bytes.decode("utf-8"))
        store = cls()
        for tsp in root.findall(".//tsl:TrustServiceProvider", TSL_NS):
            trade_name_el = tsp.find(".//tsl:TSPTradeName/tsl:Name", TSL_NS)
            ca_id = trade_name_el.text.strip() if trade_name_el is not None else None
            if not ca_id:
                continue
            for cert_el in tsp.findall(
                ".//tsl:ServiceDigitalIdentity/tsl:DigitalId/tsl:X509Certificate",
                TSL_NS,
            ):
                if not cert_el.text:
                    continue
                try:
                    der = base64.b64decode(cert_el.text.strip())
                    cert = x509.load_der_x509_certificate(der)
                    store._certs.setdefault(ca_id, []).append(CertEntry(ca_id=ca_id, cert=cert))
                except Exception:
                    continue
        return store

    @classmethod
    def default(cls) -> "TrustStore":
        """
        Return a module-level singleton loaded from the bundled TSL.

        Subsequent calls return the same cached instance (no re-parsing).
        """
        global _DEFAULT_STORE
        if _DEFAULT_STORE is None:
            _DEFAULT_STORE = cls.from_bundled_tsl()
        return _DEFAULT_STORE

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, ca_id: str) -> List[CertEntry]:
        """Return all certificates for a given CA ID."""
        return self._certs.get(ca_id, [])

    def all_entries(self) -> List[CertEntry]:
        """Return all certificate entries in the store."""
        result = []
        for entries in self._certs.values():
            result.extend(entries)
        return result

    def ca_ids(self) -> List[str]:
        """Return the list of CA IDs in the store."""
        return list(self._certs.keys())

    def merge(self, other: "TrustStore") -> "TrustStore":
        """Return a new TrustStore combining self and other."""
        merged = TrustStore()
        merged._certs = {k: list(v) for k, v in self._certs.items()}
        for ca_id, entries in other._certs.items():
            merged._certs.setdefault(ca_id, []).extend(entries)
        return merged

    def __len__(self) -> int:
        return sum(len(v) for v in self._certs.values())

    def __repr__(self) -> str:
        total = len(self)
        cas = ", ".join(sorted(self._certs))
        return f"<TrustStore {total} cert(s) for CA(s): {cas}>"

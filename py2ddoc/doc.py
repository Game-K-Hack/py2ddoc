"""
High-level 2D-Doc document class.

This is the main entry point for most users::

    from py2ddoc import TwoDDoc

    # Uses the bundled ANTS TSL automatically — no external file needed
    doc = TwoDDoc.from_string(barcode_content)

    print(doc.doc_type_label)    # "Avis d'imposition"
    print(doc.is_authentic)      # True / False
    print(doc.fields)            # {"01": "12345678901234", ...}
    print(doc.named_fields)      # {"numero_avis": "12345678901234", ...}
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import CertificateNotFoundError, ParseError, SignatureError
from .fields import get_doc_type_label, get_field_def
from .parser import ParsedDoc, parse
from .tsl import CertEntry, TrustStore
from . import verifier as _verifier


class TwoDDoc:
    """
    A decoded (and optionally verified) 2D-Doc barcode.

    Attributes:
        version:       2D-Doc version string (e.g. ``"03"``).
        ca_id:         Certification authority identifier (e.g. ``"FR01"``).
        cert_id:       Signing certificate identifier within the CA.
        doc_date:      Date of document issuance (``date`` or ``None``).
        sign_date:     Date of electronic signature (``date`` or ``None``).
        doc_type:      4-char document type code (e.g. ``"0001"``).
        fields:        Raw field dict ``{field_id: value}``.
        is_authentic:  ``True`` if signature was verified, ``False`` otherwise,
                       ``None`` if verification was not attempted.
        signing_cert:  The :class:`~py2ddoc.tsl.CertEntry` used to verify, or ``None``.
    """

    def __init__(self, parsed: ParsedDoc):
        self._parsed = parsed
        self.is_authentic: Optional[bool] = None
        self.signing_cert: Optional[CertEntry] = None
        self._verify_error: Optional[str] = None

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_string(
        cls,
        content: str | bytes,
        trust_store: Optional[TrustStore] = None,
        verify: bool = True,
    ) -> "TwoDDoc":
        """
        Parse and verify a 2D-Doc barcode string.

        By default, signature verification is performed automatically using
        the ANTS TSL bundled with the package (no external file required).

        Args:
            content:     Raw barcode content (string or bytes).
            trust_store: Custom :class:`~py2ddoc.tsl.TrustStore` to use for
                         verification. Defaults to the bundled ANTS TSL.
            verify:      Set to ``False`` to skip signature verification entirely.

        Returns:
            A :class:`TwoDDoc` instance.

        Raises:
            ParseError: If *content* is not a valid 2D-Doc barcode.
        """
        parsed = parse(content)
        doc = cls(parsed)
        if verify:
            store = trust_store if trust_store is not None else TrustStore.default()
            doc.verify(store)
        return doc

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self, trust_store: TrustStore) -> bool:
        """
        Verify the digital signature against *trust_store*.

        Updates :attr:`is_authentic` and :attr:`signing_cert` in place.

        Returns:
            ``True`` if the signature is valid.

        Raises:
            CertificateNotFoundError: No matching certificate in store.
            SignatureError: Signature is present but invalid.
        """
        try:
            entry = _verifier.verify(self._parsed, trust_store)
            self.signing_cert = entry
            self.is_authentic = True
            return True
        except (CertificateNotFoundError, SignatureError) as exc:
            self.is_authentic = False
            self._verify_error = str(exc)
            raise

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def version(self) -> str:
        return self._parsed.version

    @property
    def ca_id(self) -> str:
        return self._parsed.ca_id

    @property
    def cert_id(self) -> str:
        return self._parsed.cert_id

    @property
    def doc_date(self) -> Optional[date]:
        return self._parsed.doc_date

    @property
    def sign_date(self) -> Optional[date]:
        return self._parsed.sign_date

    @property
    def doc_type(self) -> str:
        return self._parsed.doc_type

    @property
    def doc_type_label(self) -> str:
        """Human-readable label for the document type."""
        return get_doc_type_label(self._parsed.doc_type)

    @property
    def fields(self) -> Dict[str, str]:
        """Raw field dict ``{field_id: raw_value}``."""
        return dict(self._parsed.fields)

    @property
    def named_fields(self) -> Dict[str, str]:
        """
        Field dict keyed by field *name* instead of ID.

        Fields with no definition in :mod:`py2ddoc.fields` are kept
        under their original 2-char ID.
        """
        result: Dict[str, str] = {}
        for fid, val in self._parsed.fields.items():
            defn = get_field_def(self._parsed.doc_type, fid)
            key = defn.name if defn else fid
            result[key] = val
        return result

    @property
    def raw(self) -> str:
        """The full raw barcode string."""
        return self._parsed.raw

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the document to a plain dictionary."""
        return {
            "version": self.version,
            "ca_id": self.ca_id,
            "cert_id": self.cert_id,
            "doc_type": self.doc_type,
            "doc_type_label": self.doc_type_label,
            "doc_date": self.doc_date.isoformat() if self.doc_date else None,
            "sign_date": self.sign_date.isoformat() if self.sign_date else None,
            "fields": self.fields,
            "named_fields": self.named_fields,
            "is_authentic": self.is_authentic,
            "signing_cert": str(self.signing_cert) if self.signing_cert else None,
        }

    def __repr__(self) -> str:
        authentic_str = (
            "authentic" if self.is_authentic
            else ("INVALID" if self.is_authentic is False else "unverified")
        )
        return (
            f"<TwoDDoc v{self.version} type={self.doc_type!r} "
            f"({self.doc_type_label}) ca={self.ca_id!r} {authentic_str}>"
        )

    def __str__(self) -> str:
        lines = [
            f"2D-Doc v{self.version}",
            f"  Type         : {self.doc_type} — {self.doc_type_label}",
            f"  CA / Cert    : {self.ca_id} / {self.cert_id}",
            f"  Doc date     : {self.doc_date}",
            f"  Sign date    : {self.sign_date}",
            f"  Authenticity : {'✓ verified' if self.is_authentic else ('✗ INVALID' if self.is_authentic is False else 'not verified')}",
            "  Fields:",
        ]
        for fid, val in self._parsed.fields.items():
            defn = get_field_def(self._parsed.doc_type, fid)
            label = defn.description if defn else fid
            lines.append(f"    [{fid}] {label}: {val}")
        return "\n".join(lines)


Doc2D = TwoDDoc  # backwards-compatible alias

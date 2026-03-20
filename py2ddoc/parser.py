"""
Low-level parsing of 2D-Doc barcode content.

2D-Doc v3 structure (ISO-8859-1 encoded):
  DC03<CA_ID:4><CERT_ID:4><DOC_DATE:4><SIGN_DATE:4><DOC_TYPE:4>
  <FIELD_ID:2><VALUE>[\x1D<FIELD_ID:2><VALUE>...]
  \x1F
  <SIGNATURE_BASE32>

Dates are encoded as 4-char base-36 integers (days since 2000-01-01).
\x1D (GS) separates data fields.
\x1F (US) separates message from signature.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from .exceptions import ParseError

# Control characters
GROUP_SEP = "\x1d"   # Separates data fields
UNIT_SEP = "\x1f"    # Separates message from signature

HEADER_MARKER = "DC"
HEADER_LENGTH = 24   # DC(2) + version(2) + CA(4) + cert(4) + docdate(4) + signdate(4) + doctype(4)

BASE_DATE = date(2000, 1, 1)

SUPPORTED_VERSIONS = {"02", "03", "04"}


def _b36_to_date(raw: str) -> Optional[date]:
    """Decode a 4-char base-36 string to a date (days since 2000-01-01)."""
    if not raw or raw == "0000":
        return None
    try:
        days = int(raw, 36)
        return BASE_DATE + timedelta(days=days)
    except (ValueError, OverflowError):
        return None


def _decode_content(raw: bytes | str) -> str:
    """Ensure content is a string, trying UTF-8 then Latin-1."""
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


@dataclass
class ParsedDoc:
    """Result of parsing a 2D-Doc barcode."""
    raw: str
    version: str
    ca_id: str
    cert_id: str
    doc_date: Optional[date]
    sign_date: Optional[date]
    doc_type: str
    fields: Dict[str, str]
    message: str           # Header + data (the signed part)
    signature_b32: str     # Base-32 encoded raw signature bytes

    @property
    def signature_bytes(self) -> bytes:
        """Decode the base-32 signature to raw bytes."""
        s = self.signature_b32.upper()
        # Add padding to make length a multiple of 8
        pad = (8 - len(s) % 8) % 8
        return base64.b32decode(s + "=" * pad)


def parse(content: bytes | str) -> ParsedDoc:
    """
    Parse a 2D-Doc barcode string.

    Args:
        content: Raw barcode string (str or bytes).

    Returns:
        ParsedDoc instance with all extracted fields.

    Raises:
        ParseError: If the content is not a valid 2D-Doc barcode.
    """
    text = _decode_content(content)

    # Split on unit separator
    if UNIT_SEP not in text:
        raise ParseError(
            "No unit separator (\\x1f) found — content is not a valid 2D-Doc barcode"
        )

    us_pos = text.index(UNIT_SEP)
    message = text[:us_pos]
    signature_b32 = text[us_pos + 1:]

    if not signature_b32:
        raise ParseError("Signature part is empty")

    # Validate and parse header
    if len(message) < HEADER_LENGTH:
        raise ParseError(
            f"Message too short ({len(message)} chars); "
            f"expected at least {HEADER_LENGTH} chars for the header"
        )

    if not message.startswith(HEADER_MARKER):
        raise ParseError(
            f"Message does not start with '{HEADER_MARKER}' — "
            f"got {message[:2]!r}"
        )

    version = message[2:4]
    if version not in SUPPORTED_VERSIONS:
        raise ParseError(
            f"Unsupported 2D-Doc version '{version}'; "
            f"supported: {sorted(SUPPORTED_VERSIONS)}"
        )

    ca_id = message[4:8]
    cert_id = message[8:12]
    doc_date = _b36_to_date(message[12:16])
    sign_date = _b36_to_date(message[16:20])
    doc_type = message[20:24]

    # Parse data fields (after the 24-char header)
    data_str = message[HEADER_LENGTH:]
    fields: Dict[str, str] = {}

    if data_str:
        parts = data_str.split(GROUP_SEP)
        for part in parts:
            if len(part) >= 2:
                fid = part[:2]
                fval = part[2:]
                fields[fid] = fval

    return ParsedDoc(
        raw=text,
        version=version,
        ca_id=ca_id,
        cert_id=cert_id,
        doc_date=doc_date,
        sign_date=sign_date,
        doc_type=doc_type,
        fields=fields,
        message=message,
        signature_b32=signature_b32,
    )

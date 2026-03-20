"""Tests for the 2D-Doc parser."""

import pytest
from datetime import date

from py2ddoc import parse, ParsedDoc
from py2ddoc.exceptions import ParseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_barcode(
    version="03",
    ca_id="FR01",
    cert_id="0001",
    doc_date="0P00",   # base36: 0P00 = some date
    sign_date="0P00",
    doc_type="0001",
    data="01value1\x1d02value2",
    signature="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
):
    header = f"DC{version}{ca_id}{cert_id}{doc_date}{sign_date}{doc_type}"
    return f"{header}{data}\x1f{signature}"


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------

class TestHeaderParsing:
    def test_version_extracted(self):
        raw = _make_barcode(version="03")
        doc = parse(raw)
        assert doc.version == "03"

    def test_ca_id_extracted(self):
        raw = _make_barcode(ca_id="FR03")
        doc = parse(raw)
        assert doc.ca_id == "FR03"

    def test_cert_id_extracted(self):
        raw = _make_barcode(cert_id="AB12")
        doc = parse(raw)
        assert doc.cert_id == "AB12"

    def test_doc_type_extracted(self):
        raw = _make_barcode(doc_type="000C")
        doc = parse(raw)
        assert doc.doc_type == "000C"

    def test_date_zero_is_none(self):
        raw = _make_barcode(doc_date="0000", sign_date="0000")
        doc = parse(raw)
        assert doc.doc_date is None
        assert doc.sign_date is None

    def test_date_base36_decoded(self):
        # base36("010O") = 1*36^3 + 1*36^2 + 0*36 + 24 = 46656 + 1296 + 24 = 47976 days
        # 2000-01-01 + 47976 days = let's just check it returns a date
        raw = _make_barcode(doc_date="010O")
        doc = parse(raw)
        assert isinstance(doc.doc_date, date)


# ---------------------------------------------------------------------------
# Data field parsing
# ---------------------------------------------------------------------------

class TestFieldParsing:
    def test_single_field(self):
        raw = _make_barcode(data="01hello")
        doc = parse(raw)
        assert doc.fields == {"01": "hello"}

    def test_multiple_fields(self):
        raw = _make_barcode(data="01hello\x1d02world\x1d03!")
        doc = parse(raw)
        assert doc.fields == {"01": "hello", "02": "world", "03": "!"}

    def test_empty_data(self):
        raw = _make_barcode(data="")
        doc = parse(raw)
        assert doc.fields == {}

    def test_field_with_empty_value(self):
        raw = _make_barcode(data="01\x1d02value")
        doc = parse(raw)
        assert doc.fields["01"] == ""
        assert doc.fields["02"] == "value"


# ---------------------------------------------------------------------------
# Signature extraction
# ---------------------------------------------------------------------------

class TestSignature:
    def test_signature_extracted(self):
        sig = "MYREALBASE32SIG"
        raw = _make_barcode(signature=sig)
        doc = parse(raw)
        assert doc.signature_b32 == sig

    def test_message_is_before_unit_sep(self):
        raw = _make_barcode(data="01test")
        doc = parse(raw)
        assert "\x1f" not in doc.message
        assert doc.message.startswith("DC")


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestParseErrors:
    def test_missing_unit_separator(self):
        with pytest.raises(ParseError, match="unit separator"):
            parse("DC030001000100000000000101hello")

    def test_wrong_marker(self):
        with pytest.raises(ParseError, match="DC"):
            raw = _make_barcode()
            parse("XX" + raw[2:])

    def test_unsupported_version(self):
        with pytest.raises(ParseError, match="version"):
            parse(_make_barcode(version="99"))

    def test_too_short(self):
        with pytest.raises(ParseError):
            parse("DC03FR\x1fABC")

    def test_empty_signature(self):
        with pytest.raises(ParseError, match="empty"):
            parse("DC03FR010001000000000001\x1f")


# ---------------------------------------------------------------------------
# Bytes input
# ---------------------------------------------------------------------------

class TestBytesInput:
    def test_utf8_bytes(self):
        raw = _make_barcode()
        doc = parse(raw.encode("utf-8"))
        assert doc.version == "03"

    def test_latin1_bytes(self):
        raw = _make_barcode(data="01café")
        doc = parse(raw.encode("latin-1"))
        assert "café" in doc.fields.get("01", "")

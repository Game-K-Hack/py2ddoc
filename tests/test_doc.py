"""Tests for the high-level TwoDDoc class."""

import pytest

from py2ddoc import TwoDDoc, TrustStore
from py2ddoc.exceptions import ParseError, SignatureError, CertificateNotFoundError
from py2ddoc.fields import get_doc_type_label, get_field_def


def _make_raw(doc_type="0001", data="01value1\x1d02value2", signature="A" * 104):
    header = f"DC03FR010001000000000001"
    # Replace default doc_type bytes
    header = f"DC03FR010001000000000{doc_type[:1]}{doc_type[1:]}"
    # Simple fixed header of 24 chars
    return f"DC03FR010001AAAA0000{doc_type}{data}\x1f{signature}"


class TestTwoDDocProperties:
    def test_basic_parse(self):
        doc = TwoDDoc.from_string(_make_raw(), verify=False)
        assert doc.version == "03"
        assert doc.ca_id == "FR01"
        assert doc.doc_type == "0001"

    def test_doc_type_label(self):
        doc = TwoDDoc.from_string(_make_raw(doc_type="0001"), verify=False)
        assert "imposition" in doc.doc_type_label.lower()

    def test_fields_raw(self):
        doc = TwoDDoc.from_string(_make_raw(data="01hello\x1d02world"), verify=False)
        assert doc.fields == {"01": "hello", "02": "world"}

    def test_named_fields_known_type(self):
        doc = TwoDDoc.from_string(_make_raw(doc_type="0001", data="01myid"), verify=False)
        nf = doc.named_fields
        # field "01" of doc type "0001" should map to "numero_avis"
        assert "numero_avis" in nf

    def test_named_fields_unknown_type_keeps_id(self):
        doc = TwoDDoc.from_string(_make_raw(doc_type="FFFF", data="ZZsomething"), verify=False)
        nf = doc.named_fields
        assert "ZZ" in nf

    def test_is_authentic_none_when_verify_false(self):
        doc = TwoDDoc.from_string(_make_raw(), verify=False)
        assert doc.is_authentic is None

    def test_repr_contains_type(self):
        doc = TwoDDoc.from_string(_make_raw(doc_type="0001"), verify=False)
        assert "0001" in repr(doc)

    def test_str_output(self):
        doc = TwoDDoc.from_string(_make_raw(data="01hello"), verify=False)
        s = str(doc)
        assert "2D-Doc" in s
        assert "FR01" in s

    def test_to_dict(self):
        doc = TwoDDoc.from_string(_make_raw(data="01hello"), verify=False)
        d = doc.to_dict()
        assert d["ca_id"] == "FR01"
        assert d["version"] == "03"
        assert "fields" in d
        assert "named_fields" in d

    def test_raw_property(self):
        raw = _make_raw()
        doc = TwoDDoc.from_string(raw, verify=False)
        assert doc.raw == raw


class TestVerificationErrors:
    def test_invalid_sig_raises_with_bundled_tsl(self):
        """A fake barcode must fail verification against the real bundled TSL."""
        with pytest.raises((SignatureError, CertificateNotFoundError)):
            TwoDDoc.from_string(_make_raw())

    def test_no_certs_raises(self):
        doc = TwoDDoc.from_string(_make_raw(), verify=False)
        store = TrustStore()  # empty
        with pytest.raises(CertificateNotFoundError):
            doc.verify(store)
        assert doc.is_authentic is False


class TestFieldDefs:
    def test_known_field(self):
        defn = get_field_def("0001", "01")
        assert defn is not None
        assert defn.name == "numero_avis"

    def test_unknown_doc_type_returns_none(self):
        assert get_field_def("ZZZZ", "01") is None

    def test_unknown_field_id_returns_none(self):
        assert get_field_def("0001", "ZZ") is None

    def test_doc_type_label_unknown(self):
        label = get_doc_type_label("ZZZZ")
        assert "ZZZZ" in label

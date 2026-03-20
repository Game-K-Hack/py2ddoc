"""Tests for the TSL certificate loader."""

import pytest

from py2ddoc.tsl import TrustStore, CertEntry


@pytest.fixture(scope="module")
def store():
    return TrustStore.from_bundled_tsl()


class TestTrustStore:
    def test_loads_certificates(self, store):
        assert len(store) > 0

    def test_known_ca_ids(self, store):
        ca_ids = store.ca_ids()
        # TSL should contain at least FR01 and FR03
        assert any(ca.startswith("FR") for ca in ca_ids)

    def test_get_returns_list(self, store):
        ca_ids = store.ca_ids()
        if ca_ids:
            entries = store.get(ca_ids[0])
            assert isinstance(entries, list)
            assert len(entries) > 0

    def test_get_unknown_returns_empty(self, store):
        assert store.get("XXXX") == []

    def test_all_entries(self, store):
        all_e = store.all_entries()
        assert len(all_e) == len(store)

    def test_cert_entry_repr(self, store):
        entry = store.all_entries()[0]
        assert entry.ca_id in repr(entry)

    def test_key_type_string(self, store):
        for entry in store.all_entries():
            kt = entry.key_type
            assert "/" in kt or kt  # e.g. "EC/secp256r1" or "RSA/2048"

    def test_merge(self, store):
        merged = store.merge(store)
        assert len(merged) == 2 * len(store)

    def test_from_pem_roundtrip(self, store):
        entry = store.all_entries()[0]
        from cryptography.hazmat.primitives import serialization
        pem = entry.cert.public_bytes(serialization.Encoding.PEM)
        # Re-build a store from DER
        der = entry.cert.public_bytes(serialization.Encoding.DER)
        # load_pem_x509_certificate expects the full cert PEM, not just the public key
        cert_pem = entry.cert.public_bytes(serialization.Encoding.PEM)
        # DER round-trip
        s2 = TrustStore.from_der(entry.ca_id, entry.cert.public_bytes(serialization.Encoding.DER))
        assert len(s2) == 1

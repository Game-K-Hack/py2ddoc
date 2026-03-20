# py2ddoc

Python library to decode and verify French **ANTS 2D-Doc** barcodes (QR Code / Data Matrix).

The [2D-Doc standard](https://ants.gouv.fr/nos-missions/les-solutions-numeriques/2d-doc) is issued by the French *Agence Nationale des Titres Sécurisés* (ANTS) and is embedded in many official French documents: tax notices, pay slips, driving licences, vehicle registration certificates, social security attestations, etc.

## Features

- Parse 2D-Doc v2, v3, and v4 barcodes
- Verify ECDSA (P-256, P-384) and RSA-PKCS1v15 digital signatures
- ANTS TSL bundled — no external file required out of the box
- Decode field IDs to human-readable names for all major document types
- Pure Python — no native dependencies beyond `cryptography`

## Installation

```bash
pip install py2ddoc
```

## Quickstart

```python
from py2ddoc import TwoDDoc

# The ANTS TSL is bundled with the package — no external file needed
barcode = "DC03FR010001AAAA0000000101Jean\x1d02Dupont\x1fSIGNATURE..."
doc = TwoDDoc.from_string(barcode)

print(doc)
# 2D-Doc v03
#   Type         : 0001 — Avis d'imposition
#   CA / Cert    : FR01 / 0001
#   Doc date     : 2023-05-15
#   Sign date    : 2023-05-15
#   Authenticity : ✓ verified
#   Fields:
#     [01] Numéro de l'avis d'imposition: 12345678901234
#     ...

print(doc.is_authentic)    # True
print(doc.doc_type_label)  # "Avis d'imposition"
print(doc.fields)          # {"01": "...", "02": "..."}
print(doc.named_fields)    # {"numero_avis": "...", "nom": "..."}
```

### Parse without verification

```python
from py2ddoc import parse

parsed = parse(barcode_string)
print(parsed.ca_id)    # "FR01"
print(parsed.doc_type) # "0001"
print(parsed.fields)   # {"01": "value", ...}
```

### Load a single certificate manually

```python
from py2ddoc import TrustStore

with open("my_cert.der", "rb") as f:
    store = TrustStore.from_der("FR01", f.read())

doc = TwoDDoc.from_string(barcode, trust_store=store)

# Or from PEM:
with open("my_cert.pem", "rb") as f:
    store = TrustStore.from_pem("FR01", f.read())
```

### Merge multiple stores

```python
from py2ddoc import TrustStore, TwoDDoc

bundled = TrustStore.from_bundled_tsl()
extra = TrustStore.from_pem("FR99", open("extra.pem", "rb").read())
store = bundled.merge(extra)
doc = TwoDDoc.from_string(barcode, trust_store=store)
```

## Trust Store (TSL)

The official ANTS TSL is **bundled with this package** and loaded automatically when you call `TwoDDoc.from_string()`. No download or configuration is needed.

For advanced use cases (e.g. a custom authority or a TSL downloaded independently), you can load it explicitly:

```python
store = TrustStore.from_tsl("/path/to/tsl_signed.xml")
doc = TwoDDoc.from_string(barcode, trust_store=store)
```

The official TSL file is published by ANTS at:

```
https://pub.ants.gouv.fr/2D-DOC/V1/PRD/01_TSL/tsl_signed.xml
```

## Supported document types

| Code | Label |
|------|-------|
| 0001 | Avis d'imposition |
| 0007 | Fiche de paie |
| 0008 | Attestation Pôle Emploi |
| 000C | Permis de conduire |
| 000E | Carte nationale d'identité |
| 001A | Attestation de droits Sécurité Sociale |
| 0024 | Certificat d'immatriculation |
| … | (see `py2ddoc/fields.py` for the full list) |

## Exceptions

| Exception | Raised when |
|-----------|-------------|
| `ParseError` | Barcode content is malformed |
| `CertificateNotFoundError` | CA ID not found in trust store |
| `SignatureError` | Signature present but invalid |

All inherit from `TwoDBarcodeError`.

## License

MIT

"""
Field definitions for 2D-Doc document types.

Field IDs are 2-char alphanumeric strings, specific to each document type.
Definitions are based on ANTS 2D-Doc specification (Annexe A).
"""

from typing import Dict, NamedTuple, Optional


class FieldDef(NamedTuple):
    name: str
    description: str
    length: Optional[int] = None  # None = variable length


# Document type codes -> human-readable labels
DOCUMENT_TYPES: Dict[str, str] = {
    "0001": "Avis d'imposition",
    "0002": "Attestation de droits AME",
    "0003": "Attestation de droits CSS",
    "0004": "Attestation de versement CAF",
    "0005": "Déclaration de revenus",
    "0006": "Attestation de paiement de cotisations URSSAF",
    "0007": "Fiche de paie",
    "0008": "Attestation Pôle Emploi",
    "0009": "Relevé de situation CAF",
    "000A": "Relevé MSA",
    "000B": "Attestation d'identité",
    "000C": "Permis de conduire",
    "000D": "Passeport",
    "000E": "Carte nationale d'identité",
    "000F": "Attestation de séjour",
    "0010": "Titre de séjour",
    "0011": "Acte de naissance",
    "0012": "Attestation de décès",
    "0013": "Justificatif de domicile (EDF/GDF)",
    "0014": "Justificatif de domicile (eau)",
    "0015": "Justificatif de domicile (télécom)",
    "0016": "Justificatif de domicile (loyer)",
    "0017": "Attestation de bourse",
    "0018": "Attestation de scolarité",
    "0019": "Récépissé de dépôt de demande de titre de séjour",
    "001A": "Attestation de droits Sécurité Sociale",
    "001B": "Relevé de compte bancaire",
    "001C": "Quittance de loyer",
    "001D": "Avis de versement de pension alimentaire",
    "001E": "Certificat médical",
    "001F": "Jugement",
    "0020": "Acte notarié",
    "0021": "Contrat de travail",
    "0022": "Contrat de bail",
    "0023": "Attestation d'assurance",
    "0024": "Carte grise (certificat d'immatriculation)",
    "0025": "Certificat de cession de véhicule",
    "0026": "Procès-verbal de contrôle technique",
    "0027": "Attestation Pôle Emploi ARE",
    "0028": "Attestation d'hébergement",
    "0029": "Relevé de notes BAC",
    "002A": "Diplôme universitaire",
    "002B": "Bulletin scolaire",
    "002C": "Attestation d'enregistrement ETIAS",
}

# Field definitions: DOCUMENT_TYPE -> {FIELD_ID -> FieldDef}
FIELDS: Dict[str, Dict[str, FieldDef]] = {
    # Avis d'imposition (tax notice)
    "0001": {
        "01": FieldDef("numero_avis", "Numéro de l'avis d'imposition", 13),
        "02": FieldDef("rfr", "Revenu fiscal de référence"),
        "03": FieldDef("nb_parts", "Nombre de parts"),
        "04": FieldDef("revenu_imposable", "Revenu imposable"),
        "05": FieldDef("montant_impot", "Montant d'impôt"),
        "06": FieldDef("date_recouvrement", "Date de mise en recouvrement"),
        "07": FieldDef("annee_revenus", "Année des revenus"),
        "08": FieldDef("annee_imposition", "Année d'imposition"),
        "09": FieldDef("nom", "Nom du contribuable"),
        "0A": FieldDef("prenom", "Prénom du contribuable"),
        "0B": FieldDef("adresse", "Adresse du contribuable"),
        "0C": FieldDef("code_postal", "Code postal", 5),
        "0D": FieldDef("ville", "Ville"),
        "0E": FieldDef("situation_familiale", "Situation familiale", 1),
    },
    # Permis de conduire
    "000C": {
        "01": FieldDef("nom_naissance", "Nom de naissance"),
        "02": FieldDef("prenom", "Prénom(s)"),
        "03": FieldDef("date_naissance", "Date de naissance", 8),
        "04": FieldDef("lieu_naissance", "Lieu de naissance"),
        "05": FieldDef("date_delivrance", "Date de délivrance", 8),
        "06": FieldDef("numero_permis", "Numéro du permis"),
        "07": FieldDef("categories", "Catégories"),
        "08": FieldDef("nom_usage", "Nom d'usage"),
    },
    # Carte nationale d'identité
    "000E": {
        "01": FieldDef("nom", "Nom"),
        "02": FieldDef("prenom", "Prénom(s)"),
        "03": FieldDef("date_naissance", "Date de naissance", 8),
        "04": FieldDef("lieu_naissance", "Lieu de naissance"),
        "05": FieldDef("sexe", "Sexe", 1),
        "06": FieldDef("numero_cni", "Numéro de la CNI"),
        "07": FieldDef("date_expiration", "Date d'expiration", 8),
        "08": FieldDef("nationalite", "Nationalité", 3),
        "09": FieldDef("taille", "Taille"),
        "0A": FieldDef("nom_usage", "Nom d'usage"),
    },
    # Fiche de paie
    "0007": {
        "01": FieldDef("nom_salarie", "Nom du salarié"),
        "02": FieldDef("prenom_salarie", "Prénom du salarié"),
        "03": FieldDef("nir", "NIR (numéro de sécurité sociale)", 15),
        "04": FieldDef("emploi", "Emploi / Poste"),
        "05": FieldDef("periode_debut", "Début de la période de paie", 8),
        "06": FieldDef("periode_fin", "Fin de la période de paie", 8),
        "07": FieldDef("salaire_brut", "Salaire brut"),
        "08": FieldDef("salaire_net_avant_impot", "Salaire net avant impôt"),
        "09": FieldDef("salaire_net", "Salaire net payé"),
        "0A": FieldDef("nom_employeur", "Nom de l'employeur"),
        "0B": FieldDef("siret", "SIRET de l'employeur", 14),
        "0C": FieldDef("convention_collective", "Convention collective"),
        "0D": FieldDef("date_entree", "Date d'entrée dans l'entreprise", 8),
    },
    # Attestation de droits Sécurité Sociale
    "001A": {
        "01": FieldDef("nom", "Nom"),
        "02": FieldDef("prenom", "Prénom"),
        "03": FieldDef("date_naissance", "Date de naissance", 8),
        "04": FieldDef("nir", "NIR", 15),
        "05": FieldDef("regime", "Régime"),
        "06": FieldDef("caisse", "Caisse"),
        "07": FieldDef("date_validite", "Date de validité", 8),
        "08": FieldDef("medecin_traitant", "Médecin traitant déclaré", 1),
    },
    # Attestation Pôle Emploi
    "0008": {
        "01": FieldDef("nom", "Nom"),
        "02": FieldDef("prenom", "Prénom"),
        "03": FieldDef("date_naissance", "Date de naissance", 8),
        "04": FieldDef("nir", "NIR", 15),
        "05": FieldDef("identifiant_pe", "Identifiant Pôle Emploi"),
        "06": FieldDef("date_inscription", "Date d'inscription", 8),
        "07": FieldDef("situation", "Situation"),
        "08": FieldDef("allocation_journaliere", "Allocation journalière brute"),
    },
    # Justificatif de domicile générique (codes 0013-0016)
    "0013": {
        "01": FieldDef("nom", "Nom"),
        "02": FieldDef("prenom", "Prénom"),
        "03": FieldDef("adresse", "Adresse"),
        "04": FieldDef("code_postal", "Code postal", 5),
        "05": FieldDef("ville", "Ville"),
        "06": FieldDef("date_emission", "Date d'émission", 8),
        "07": FieldDef("emetteur", "Émetteur"),
        "08": FieldDef("contrat", "Numéro de contrat"),
    },
    # Certificat d'immatriculation (carte grise)
    "0024": {
        "01": FieldDef("immatriculation", "Numéro d'immatriculation"),
        "02": FieldDef("vin", "VIN (numéro de série)", 17),
        "03": FieldDef("marque", "Marque"),
        "04": FieldDef("modele", "Modèle / Type"),
        "05": FieldDef("date_premiere_immatriculation", "Date de 1ère immatriculation", 8),
        "06": FieldDef("nom_proprietaire", "Nom du propriétaire"),
        "07": FieldDef("prenom_proprietaire", "Prénom du propriétaire"),
        "08": FieldDef("adresse_proprietaire", "Adresse du propriétaire"),
        "09": FieldDef("puissance_fiscale", "Puissance fiscale"),
        "0A": FieldDef("energie", "Source d'énergie"),
        "0B": FieldDef("poids_total", "PTAC"),
    },
}

# Aliases for document types that share the same field structure
for _alias in ("0014", "0015", "0016"):
    FIELDS[_alias] = FIELDS["0013"]


def get_field_def(doc_type: str, field_id: str) -> Optional[FieldDef]:
    """Return the FieldDef for a given document type and field ID, or None."""
    return FIELDS.get(doc_type, {}).get(field_id)


def get_doc_type_label(doc_type: str) -> str:
    """Return the human-readable label for a document type code."""
    return DOCUMENT_TYPES.get(doc_type, f"Type inconnu ({doc_type})")

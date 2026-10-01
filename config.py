# Configuration pour l'application EduPaie
# Devise et formatage des montants

# Devise
DEVISE = "FCFA"

# Plafond maximum pour les montants (en FCFA)
MONTANT_MAX = 1000000

# Suffixe pour l'affichage des montants
FORMAT_MONTANT_SUFFIX = " FCFA"

def format_montant(montant: float) -> str:
    """Formate un montant pour l'affichage"""
    return f"{int(montant):,} {DEVISE}".replace(",", " ")

def calculate_payment_status(balance: float, total: float) -> str:
    """Détermine le statut de paiement"""
    if balance <= 0:
        return "Soldé"
    elif balance < total:
        return "Partiellement payé"
    else:
        return "Non payé"

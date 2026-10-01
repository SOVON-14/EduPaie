# -*- coding: utf-8 -*-
"""Configuration globale d'EduPaie.

Correction CRIT-02 de l'audit : la devise était incohérente selon les
écrans (FCFA dans le formulaire élève, EUR partout ailleurs). Elle est
désormais définie en un seul endroit : changer DEVISE ici suffit pour
toute l'application (formulaires, tableaux, messages, reçus PDF).
"""

# Devise affichée partout dans l'application (une par installation)
DEVISE = "FCFA"

# Le FCFA n'a pas de sous-unité : aucune décimale.
# (Mettre 2 pour une devise à centimes comme l'EUR.)
DECIMALES = 0

# Plafond de saisie des montants (montant total dû d'un élève comme
# montant d'un paiement). Corrige au passage IMP-03 : le plafond de
# paiement (100 000) était inférieur au total dû possible (1 000 000).
MONTANT_MAX = 100_000_000

# Suffixe prêt à l'emploi pour les QDoubleSpinBox
FORMAT_MONTANT_SUFFIX = f" {DEVISE}"


def format_montant(valeur: float) -> str:
    """Formate un montant monétaire avec la devise de l'application.

    Exemple (FCFA) : format_montant(150000) -> "150 000 FCFA"
    """
    if DECIMALES == 0:
        texte = f"{valeur:,.0f}".replace(",", " ")
    else:
        texte = f"{valeur:,.{DECIMALES}f}".replace(",", " ")
    return f"{texte} {DEVISE}"


def calculate_payment_status(balance: float, total: float) -> str:
    """Calcule le statut de paiement de manière centralisée.

    La logique est utilisée dans plusieurs services pour garantir une
    cohérence totale entre les écrans, le tableau de bord et les reçus.
    """
    if balance <= 0:
        return "Soldé"
    if balance < total:
        return "Partiellement payé"
    return "Non payé"

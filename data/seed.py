# -*- coding: utf-8 -*-
"""Jeu de données de démonstration pour EduPaie (montants en FCFA).

Crée quelques élèves avec des statuts de paiement variés (soldé, partiel,
non payé) pour tester le tableau de bord, l'historique et les reçus PDF.

Utilisation :
    python data/seed.py

Le script ne fait rien si la base contient déjà des élèves (sécurité) ;
purger la base manuellement pour relancer une initialisation propre.
"""

import os
import sys

# Permet l'exécution directe : python data/seed.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import ensure_database_exists, get_connection
from services.payment_service import PaymentService
from services.student_service import StudentService
from config import format_montant

# (nom, prénom, classe, année scolaire, montant total, liste de paiements)
# Chaque paiement : (montant, mode_paiement)
ELEVES_DEMO = [
    ("DIALLO", "Aminata", "6ème A", "2025-2026", 250_000,
     [(100_000, "especes")]),
    ("TRAORE", "Ibrahim", "6ème B", "2025-2026", 250_000,
     [(250_000, "mobile_money")]),
    ("KONE", "Fatoumata", "5ème A", "2025-2026", 300_000,
     [(150_000, "especes"), (150_000, "cheque")]),
    ("OUEDRAOGO", "Salif", "4ème B", "2025-2026", 300_000,
     []),
    ("ZONGO", "Mariam", "3ème A", "2025-2026", 350_000,
     [(200_000, "virement")]),
    ("SANOGO", "Adama", "Terminale C", "2025-2026", 450_000,
     []),
]


def seed():
    """Insère les données de démonstration si la base est vide."""
    ensure_database_exists()

    student_service = StudentService()
    payment_service = PaymentService()

    # Sécurité : ne jamais écraser des données existantes
    with get_connection() as conn:
        nb_eleves = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    if nb_eleves > 0:
        print(f"Base non vide ({nb_eleves} élèves) : seed annulé.")
        print("Purger la base d'abord si vous souhaitez réinitialiser.")
        return

    for nom, prenom, classe, annee, montant_total, paiements in ELEVES_DEMO:
        student_id = student_service.create_student(
            nom, prenom, classe, annee, float(montant_total)
        )
        for montant, mode in paiements:
            payment_service.create_payment(student_id, float(montant), mode)
        solde = montant_total - sum(m for m, _ in paiements)
        statut = "Soldé" if solde <= 0 else (
            "Partiellement payé" if solde < montant_total else "Non payé"
        )
        print(
            f"  + {nom} {prenom} ({classe}) : "
            f"{format_montant(montant_total)} — {statut}"
        )

    print("\nSeed terminé : 6 élèves de démonstration créés (FCFA).")


if __name__ == "__main__":
    seed()

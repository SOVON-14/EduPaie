# -*- coding: utf-8 -*-
"""Jeu de données de démonstration pour EduPaie (montants en FCFA).

Crée au moins 15 élèves avec des statuts de paiement variés (soldé, partiel,
non payé) pour tester le tableau de bord, l'historique et les reçus PDF.

Utilisation :
    python data/seed.py --database data/edupaie_test.db

Le script ne fait rien si la base cible contient déjà des élèves (sécurité).
Utiliser un nouveau chemin de base pour générer un autre jeu de démonstration.
"""

import argparse
import os
import sys
from pathlib import Path

# Permet l'exécution directe : python data/seed.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import ensure_database_exists, get_connection
import database.database as database
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
    ("SIDIBE", "Mariam", "6ème A", "2025-2026", 250_000,
     [(50_000, "especes"), (75_000, "mobile_money")]),
    ("BARRY", "Moussa", "5ème B", "2025-2026", 300_000,
     []),
    ("CAMARA", "Awa", "4ème A", "2025-2026", 320_000,
     [(320_000, "cheque")]),
    ("TOURE", "Boubacar", "3ème B", "2025-2026", 350_000,
     [(100_000, "virement"), (100_000, "especes")]),
    ("KABORE", "Aicha", "Terminale A", "2025-2026", 450_000,
     []),
    ("NDIAYE", "Mamadou", "2nde C", "2025-2026", 400_000,
     [(150_000, "mobile_money"), (250_000, "virement")]),
    ("FOFANA", "Aminata", "6ème B", "2025-2026", 260_000,
     [(60_000, "cheque")]),
    ("COULIBALY", "Issa", "5ème C", "2025-2026", 300_000,
     []),
    ("SAWADOGO", "Hawa", "4ème C", "2025-2026", 320_000,
     [(100_000, "especes"), (100_000, "cheque"), (120_000, "mobile_money")]),
    ("TANDIA", "Karim", "3ème A", "2025-2026", 350_000,
     [(175_000, "virement")]),
    ("KONE", "Aissata", "2nde A", "2025-2026", 400_000,
     []),
    ("BADO", "Oumar", "Terminale C", "2025-2026", 500_000,
     [(300_000, "mobile_money"), (100_000, "especes")]),
]


def seed(database_path=None):
    """Insère les données de démonstration si la base est vide."""
    previous_db_path = database.DB_PATH
    if database_path is not None:
        database.DB_PATH = Path(database_path)

    try:
        _seed_empty_database()
    finally:
        database.DB_PATH = previous_db_path


def _seed_empty_database():
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

    print(f"\nSeed terminé : {len(ELEVES_DEMO)} élèves de démonstration créés (FCFA).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Créer un jeu de données de démonstration EduPaie.")
    parser.add_argument(
        "--database",
        type=Path,
        help="Chemin de la base SQLite à remplir (par défaut, base de l'application).",
    )
    seed(parser.parse_args().database)

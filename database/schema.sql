-- Schéma v1 (corrections IMP-04, DB-02 et DB-03 de l'audit) :
--   - montants en entiers (le FCFA n'a pas de sous-unité) ;
--   - CHECK(montant > 0) en base, pas seulement dans les services ;
--   - UNIQUE(nom, prenom, classe, annee_scolaire) contre les doublons d'élèves.
-- La migration des bases anciennes (schéma v0 : montants REAL, sans
-- contraintes) est prise en charge par database.migrate_schema().

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    classe TEXT NOT NULL,
    annee_scolaire TEXT NOT NULL,
    montant_total INTEGER NOT NULL CHECK(montant_total > 0),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nom, prenom, classe, annee_scolaire)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    montant INTEGER NOT NULL CHECK(montant > 0),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode_paiement TEXT NOT NULL CHECK(mode_paiement IN ('especes', 'cheque', 'virement', 'mobile_money')),
    numero_recu TEXT NOT NULL UNIQUE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_payments_student_id ON payments(student_id);
CREATE INDEX IF NOT EXISTS idx_students_classe ON students(classe);

-- Schéma v2 (ajout de la table settings pour les paramètres de l'établissement) :
--   - table settings pour stocker le nom de l'établissement, du directeur et la signature
-- Schéma v1 (corrections IMP-04, DB-02 et DB-03 de l'audit) :
--   - montants en entiers (le FCFA n'a pas de sous-unité) ;
--   - CHECK(montant > 0) en base, pas seulement dans les services ;
--   - UNIQUE(nom, prenom, classe, annee_scolaire) contre les doublons d'élèves.
-- La migration des bases anciennes (schéma v0 : montants REAL, sans
-- contraintes) est prise en charge par database.migrate_schema().
-- La version du schéma est suivie via PRAGMA user_version dans database.py

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

-- Table settings pour les paramètres de l'établissement (v2)
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Données par défaut pour les paramètres
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('etablissement_nom', 'Établissement Scolaire'),
    ('directeur_nom', 'Directeur'),
    ('signature_path', '');

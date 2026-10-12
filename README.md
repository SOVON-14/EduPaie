# EduPaie

[![Télécharger EduPaie](https://img.shields.io/badge/Télécharger-EduPaie-blue?style=for-the-badge&logo=windows)](dist/EduPaie-Setup.exe)

Application Python de gestion des frais de scolarité pour un établissement scolaire.

## 📋 Vue d'ensemble

EduPaie permet de :
- ✅ Gérer les élèves (ajout, modification, suppression)
- ✅ Enregistrer les paiements avec génération automatique de reçus
- ✅ Suivre le solde restant et le statut de paiement
- ✅ Générer des reçus PDF personnalisés
- ✅ Consulter le tableau de bord global et par classe
- ✅ **Importer des élèves depuis un fichier Excel**
- ✅ **Exporter des rapports PDF (tableau de bord, liste élèves, par classe)**
- ✅ **Configurer l'établissement (nom, directeur, signature avec export SVG)**

## Prérequis

- Python 3.10 ou plus récent
- Windows 10/11 (application conçue pour un usage desktop local)
- Accès au système de fichiers local pour la base SQLite

## Environnement reproductible

Le projet est conçu pour fonctionner dans un environnement virtuel dédié.

### 1) Créer l'environnement

PowerShell :

```powershell
cd "C:\Users\USER\Desktop\EduPaie"
py -3 -m venv .venv
```

### 2) Installer les dépendances

```powershell
cd "C:\Users\USER\Desktop\EduPaie"
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3) Lancer l'application

```powershell
cd "C:\Users\USER\Desktop\EduPaie"
.\.venv\Scripts\Activate.ps1
python main.py
```

## Lancement standardisé

Deux scripts sont fournis pour normaliser le démarrage :

- `scripts/setup_env.ps1` : crée l'environnement virtuel et installe les dépendances
- `scripts/run_app.ps1` : lance l'application à partir de l'environnement virtuel

Exemples :

```powershell
cd "C:\Users\USER\Desktop\EduPaie"
./scripts/setup_env.ps1
./scripts/run_app.ps1
```

## Tests

Pour valider rapidement le projet :

```powershell
cd "C:\Users\USER\Desktop\EduPaie"
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
```

## Jeu de données de démonstration

Pour ajouter les élèves de démonstration à la base utilisée par l'application sans remplacer les dossiers existants :

```powershell
.\.venv\Scripts\python.exe data\seed.py --merge --database data\edupaie.db
```

La fusion ignore les élèves déjà présents et leurs paiements. Le script de build inclut `data/edupaie.db` dans la distribution lorsqu'elle existe, afin que l'application partagée démarre avec cette base.

## Build / diffusion locale

Pour produire une version exécutable du projet localement :

```powershell
cd "C:\Users\USER\Desktop\EduPaie"
./scripts/build_app.ps1
```

Le script crée un dossier `dist/EduPaie` avec une version de l’application prête à lancer.

## Installateur Windows

Installez Inno Setup 6, puis créez l'installateur par utilisateur avec :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\build_app.ps1 -Installer
```

Le fichier `dist/EduPaie-Setup.exe` installe l'application dans le profil utilisateur, crée un raccourci et propose de lancer EduPaie à la fin. La base et les reçus sont conservés dans `%LOCALAPPDATA%\EduPaie`, séparément des fichiers de l'application.

## Documentation technique

Pour régénérer le document Word éditable et son PDF avec des captures synthétiques de l'application :

```powershell
.\.venv\Scripts\python.exe generate_architecture_document.py
```

Les fichiers sont créés à la racine du projet : `Documentation_Technique_EduPaie.docx` et `Documentation_Technique_EduPaie.pdf`.

## 📁 Structure du projet

```
EduPaie/
├── main.py                      # Point d'entrée de l'application
├── config.py                    # Configuration centrale (devise, formatage)
├── app_settings.py              # Gestion du fichier de configuration INI
├── security.py                  # Gestion de l'authentification
├── requirements.txt             # Dépendances Python
├── pyproject.toml              # Configuration du projet
│
├── database/                    # Gestion de la base de données
│   ├── database.py             # Connexion, migration, initialisation
│   └── schema.sql              # Schéma SQLite (v2 avec table settings)
│
├── repositories/                # Accès aux données (pattern Repository)
│   ├── student_repository.py   # Opérations CRUD sur les élèves
│   ├── payment_repository.py   # Opérations CRUD sur les paiements
│   └── settings_repository.py  # Gestion des paramètres établissement
│
├── services/                    # Logique métier
│   ├── student_service.py      # Service de gestion des élèves
│   ├── payment_service.py      # Service de gestion des paiements
│   ├── dashboard_service.py    # Service de statistiques et tableau de bord
│   ├── receipt_service.py      # Génération des reçus PDF
│   ├── import_service.py       # Import d'élèves depuis Excel
│   ├── report_service.py       # Génération de rapports PDF
│   ├── settings_service.py     # Gestion des paramètres établissement
│   └── backup_service.py       # Sauvegarde et restauration de la base
│
├── ui/                          # Interface utilisateur (PySide6)
│   ├── main_window.py          # Fenêtre principale
│   ├── student_dialog.py       # Dialogue d'ajout/modification d'élève
│   ├── payment_dialog.py       # Dialogue d'enregistrement de paiement
│   ├── student_detail.py       # Fenêtre de détails d'un élève
│   └── settings_dialog.py      # Dialogue de paramètres établissement
│
├── tests/                       # Tests unitaires
│
├── data/                        # Données
│   ├── edupaie.db              # Base de données SQLite
│   └── seed.py                 # Script de peuplement de la base
│
├── resources/                   # Ressources (images, icônes, etc.)
│
├── scripts/                     # Scripts utilitaires
│   ├── setup_env.ps1           # Configuration de l'environnement
│   ├── run_app.ps1             # Lancement de l'application
│   └── build_app.ps1           # Build de l'exécutable
│
├── dist/                        # Distribution (après build)
│   └── EduPaie/                # Application empaquetée
│
└── docs/                        # Documentation
    ├── Documentation_Technique_EduPaie.docx
    ├── Documentation_Technique_EduPaie.pdf
    ├── Guide_Installation_EduPaie.docx
    └── Manuel_Utilisateur_EduPaie.docx
```

### Dossiers générés à l'exécution

- `receipts/` : Reçus PDF générés
- `reports/` : Rapports PDF exportés
- `signatures/` : Images de signature uploadées

## 📝 Notes

- La base SQLite est créée automatiquement si elle est absente.
- La devise par défaut est le FCFA ; elle est centralisée dans `config.py`.
- Les tests ne doivent pas modifier le cœur du projet ; ils valident le comportement métier et UI.
- Les paramètres de l'établissement (nom, directeur, signature) sont stockés dans la table `settings` de la base de données.
- Les signatures sont converties automatiquement en SVG avec encodage base64 pour l'utilisation dans les PDF.
- La migration de schéma (v1 → v2) est automatique pour les bases existantes.

## 🔧 Fonctionnalités récentes

### Import Excel
- Import massif d'élèves depuis un fichier Excel (.xlsx, .xls)
- Format attendu : Nom, Prénom, Classe, Année scolaire, Montant total
- Validation des données et rapport d'erreurs détaillé

### Export PDF
- Rapport du tableau de bord (statistiques globales + par classe)
- Liste de tous les élèves avec statuts de paiement
- Liste filtrée par classe
- Personnalisation avec nom de l'établissement et signature du directeur

### Paramètres de l'établissement
- Configuration du nom de l'établissement
- Configuration du nom du directeur
- Upload de signature (PNG, JPG, GIF, BMP)
- Export de signature en format SVG
- Intégration automatique dans tous les documents PDF générés

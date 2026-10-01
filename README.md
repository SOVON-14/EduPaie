# EduPaie

Application Python de gestion des frais de scolarité pour un établissement scolaire.

## Vue d'ensemble

EduPaie permet de :
- gérer les élèves,
- enregistrer les paiements,
- suivre le solde restant,
- générer des reçus PDF,
- consulter le tableau de bord global et par classe.

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

## Build / diffusion locale

Pour produire une version exécutable du projet localement :

```powershell
cd "C:\Users\USER\Desktop\EduPaie"
./scripts/build_app.ps1
```

Le script crée un dossier `dist/EduPaie` avec une version de l’application prête à lancer.

## Structure du projet

- `main.py` : point d'entrée
- `config.py` : configuration centrale de l'application
- `database/` : schéma SQLite et gestion de la base
- `repositories/` : accès à la base de données
- `services/` : logique métier
- `ui/` : interface PySide6
- `tests/` : tests de non-régression
- `receipts/` : fichiers PDF générés

## Notes

- La base SQLite est créée automatiquement si elle est absente.
- La devise par défaut est le FCFA ; elle est centralisée dans `config.py`.
- Les tests ne doivent pas modifier le cœur du projet ; ils valident le comportement métier et UI.

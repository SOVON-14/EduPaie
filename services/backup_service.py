"""Service de sauvegarde et restauration de la base de données EduPaie."""

import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import zipfile

from database.database import DB_PATH, USER_DATA_DIR

logger = logging.getLogger(__name__)


class BackupService:
    """Service pour la sauvegarde et la restauration de la base de données."""
    
    def __init__(self):
        self.backup_dir = USER_DATA_DIR / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """
        Crée une sauvegarde de la base de données.
        
        Args:
            backup_name: Nom personnalisé de la sauvegarde (optionnel)
            
        Returns:
            Chemin du fichier de sauvegarde créé
            
        Raises:
            FileNotFoundError: Si la base de données n'existe pas
            IOError: Si la sauvegarde échoue
        """
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Base de données introuvable: {DB_PATH}")
        
        # Générer un nom de fichier si non fourni
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"edupaie_backup_{timestamp}.zip"
        
        backup_path = self.backup_dir / backup_name
        
        try:
            # Créer une archive ZIP contenant la base de données
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(DB_PATH, DB_PATH.name)
            
            logger.info(f"Sauvegarde créée avec succès: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
            raise IOError(f"Erreur lors de la création de la sauvegarde: {e}")
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restaure une sauvegarde de la base de données.
        
        Args:
            backup_path: Chemin du fichier de sauvegarde à restaurer
            
        Returns:
            True si la restauration a réussi, False sinon
            
        Raises:
            FileNotFoundError: Si le fichier de sauvegarde n'existe pas
            IOError: Si la restauration échoue
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Fichier de sauvegarde introuvable: {backup_path}")
        
        # Créer une sauvegarde automatique avant restauration
        try:
            auto_backup = self.create_backup(f"auto_backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
            logger.info(f"Sauvegarde automatique créée avant restauration: {auto_backup}")
        except Exception as e:
            logger.warning(f"Impossible de créer une sauvegarde automatique: {e}")
        
        try:
            # Fermer toutes les connexions à la base
            # (nécessaire sous Windows pour pouvoir remplacer le fichier)
            import sqlite3
            import gc
            gc.collect()
            
            # Restaurer depuis l'archive ZIP
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(DB_PATH.parent)
            
            logger.info(f"Restauration réussie depuis: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {e}")
            raise IOError(f"Erreur lors de la restauration: {e}")
    
    def list_backups(self) -> List[Path]:
        """
        Liste toutes les sauvegardes disponibles.
        
        Returns:
            Liste des chemins des fichiers de sauvegarde
        """
        backups = list(self.backup_dir.glob("*.zip"))
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backups
    
    def delete_backup(self, backup_path: Path) -> bool:
        """
        Supprime une sauvegarde.
        
        Args:
            backup_path: Chemin du fichier de sauvegarde à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"Sauvegarde supprimée: {backup_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la sauvegarde: {e}")
            return False
    
    def get_backup_info(self, backup_path: Path) -> dict:
        """
        Récupère les informations d'une sauvegarde.
        
        Args:
            backup_path: Chemin du fichier de sauvegarde
            
        Returns:
            Dictionnaire contenant les informations de la sauvegarde
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Fichier de sauvegarde introuvable: {backup_path}")
        
        stat = backup_path.stat()
        
        return {
            'name': backup_path.name,
            'path': str(backup_path),
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime)
        }

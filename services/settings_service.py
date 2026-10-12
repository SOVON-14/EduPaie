from repositories.settings_repository import SettingsRepository
from pathlib import Path
import base64
import logging
from database.database import USER_DATA_DIR

logger = logging.getLogger(__name__)


class SettingsService:
    """Service pour la gestion des paramètres de l'établissement"""
    
    def __init__(self):
        self.settings_repo = SettingsRepository()
        self.signatures_dir = USER_DATA_DIR / "signatures"
        self.signatures_dir.mkdir(parents=True, exist_ok=True)
    
    def get_etablissement_nom(self) -> str:
        """Récupère le nom de l'établissement"""
        return self.settings_repo.get('etablissement_nom') or 'Établissement Scolaire'
    
    def set_etablissement_nom(self, nom: str) -> bool:
        """Définit le nom de l'établissement"""
        return self.settings_repo.set('etablissement_nom', nom)
    
    def get_directeur_nom(self) -> str:
        """Récupère le nom du directeur"""
        return self.settings_repo.get('directeur_nom') or 'Directeur'
    
    def set_directeur_nom(self, nom: str) -> bool:
        """Définit le nom du directeur"""
        return self.settings_repo.set('directeur_nom', nom)
    
    def get_signature_path(self) -> str:
        """Récupère le chemin de la signature"""
        return self.settings_repo.get('signature_path') or ''
    
    def set_signature_path(self, path: str) -> bool:
        """Définit le chemin de la signature"""
        return self.settings_repo.set('signature_path', path)
    
    def save_signature_image(self, source_path: str) -> str:
        """Sauvegarde une image de signature dans le dossier de l'application.
        
        Args:
            source_path: Chemin de l'image source
            
        Returns:
            Chemin de l'image sauvegardée
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {source_path}")
        
        # Copier le fichier dans le dossier signatures
        dest_path = self.signatures_dir / source.name
        import shutil
        shutil.copy2(source_path, dest_path)
        
        # Mettre à jour le chemin dans la base
        self.set_signature_path(str(dest_path))
        
        logger.info(f"Signature sauvegardée: {dest_path}")
        return str(dest_path)
    
    def convert_signature_to_svg(self, image_path: str = None, output_path: str = None) -> str:
        """Convertit une image de signature en format SVG.
        
        Args:
            image_path: Chemin de l'image source (optionnel, utilise le chemin enregistré si non fourni)
            output_path: Chemin de sortie du SVG (optionnel)
            
        Returns:
            Chemin du fichier SVG généré
        """
        if image_path is None:
            image_path = self.get_signature_path()
        
        if not image_path:
            raise ValueError("Aucune image de signature disponible")
        
        image_source = Path(image_path)
        if not image_source.exists():
            raise FileNotFoundError(f"Image non trouvée: {image_path}")
        
        if output_path is None:
            output_path = str(self.signatures_dir / f"{image_source.stem}.svg")
        
        # Lire l'image et la convertir en base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Déterminer le type MIME
        mime_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif'
        }.get(image_source.suffix.lower(), 'image/png')
        
        # Créer le SVG avec l'image embarquée
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="200" height="100" viewBox="0 0 200 100">
  <image width="200" height="100" xlink:href="data:{mime_type};base64,{image_data}" />
</svg>'''
        
        # Sauvegarder le SVG
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        logger.info(f"Signature SVG générée: {output_path}")
        return output_path
    
    def get_signature_svg_content(self) -> str:
        """Récupère le contenu SVG de la signature pour l'utiliser dans les PDF.
        
        Returns:
            Contenu SVG de la signature ou chaîne vide si non disponible
        """
        try:
            signature_path = self.get_signature_path()
            if not signature_path:
                return ""
            
            # Générer le SVG à partir de l'image
            svg_path = self.convert_signature_to_svg(signature_path)
            
            # Lire le contenu
            with open(svg_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la signature SVG: {e}")
            return ""
    
    def get_all_settings(self) -> dict:
        """Récupère tous les paramètres"""
        return self.settings_repo.get_all()

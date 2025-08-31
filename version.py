"""
Versioning information for Genera Orario App
"""

__version__ = "1.0.1"
__app_name__ = "GeneraOrarioApp"
__description__ = "Generatore di Orari Scolastici"
__author__ = "Stefania Pepe"

def get_version():
    """Restituisce la versione corrente dell'applicazione"""
    return __version__

def get_full_version():
    """Restituisce informazioni complete sulla versione"""
    return {
        "version": __version__,
        "app_name": __app_name__,
        "description": __description__,
        "author": __author__
    }


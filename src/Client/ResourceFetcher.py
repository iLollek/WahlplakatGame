import os
import sys
import logging
from typing import Optional


class ResourceFetcher:
    """Singleton Resource Fetcher for managing static content resources.
    
    Automatically determines the correct resource path based on the environment (DEV vs PROD).
    In DEV mode, resources are loaded from the 'assets' folder relative to the script.
    In PROD mode, resources are loaded from the PyInstaller temporary folder.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceFetcher, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.env = self.determine_prod_or_dev_env()
        if self.env == "DEV":
            self.basepath = self.development_resource_path() + "\\"
        elif self.env == "PROD":
            self.basepath = self.productive_resource_path() + "\\"
            
        logging.info(f'ResourceFetcher: Set Static Content Resource Path to: {self.basepath}')
        self._initialized = True
    
    def productive_resource_path(self) -> str:
        """Gets the AppData Resource Path for production environment."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
            return base_path
        except Exception:
            base_path = os.path.abspath(".")
            return base_path
    
    def development_resource_path(self) -> str:
        """Gets the assets Resource Path for development environment."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets'))
    
    def determine_prod_or_dev_env(self) -> str:
        """Determines if the environment is PROD (frozen executable) or DEV."""
        return "PROD" if getattr(sys, 'frozen', False) else "DEV"
    
    def get_resource(self, filename: str) -> str:
        """Returns the path to the Resource based on the Environment.
        
        Args:
            filename (str): The name of the File.
        
        Returns:
            filepath (str): The Path to the Resource.
        """
        logging.info(f'Resource Requested: {filename}')
        return self.basepath + filename
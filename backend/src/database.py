"""
Gestion de la connexion à Neo4j
"""
from neo4j import GraphDatabase
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Neo4jConnection:
    """Classe singleton pour gérer la connexion Neo4j"""
    
    _instance: Optional['Neo4jConnection'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        self._initialized = True
    
    def connect(self):
        """Établit la connexion à Neo4j"""
        if self.driver is None:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            print(f"✓ Connecté à Neo4j sur {self.uri}")
    
    def close(self):
        """Ferme la connexion à Neo4j"""
        if self.driver is not None:
            self.driver.close()
            self.driver = None
            print("✓ Connexion Neo4j fermée")
    
    def get_session(self):
        """Retourne une session Neo4j"""
        if self.driver is None:
            self.connect()
        return self.driver.session()
    
    def verify_connectivity(self):
        """Vérifie la connectivité avec Neo4j"""
        try:
            self.connect()
            with self.get_session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            return True
        except Exception as e:
            print(f"✗ Erreur de connexion à Neo4j : {e}")
            return False


# Instance globale
db = Neo4jConnection()

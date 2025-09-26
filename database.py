import psycopg2
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from config import get_config

class Database:
    """
    Database connection and operation handler using PostgreSQL.
    Uses configuration from config.py to establish connections.
    """
    
    def __init__(self):
        """
        Initialize the Database class.
        
        Args:
            config: Optional configuration dictionary. If None, will load from config.py
        """
        self.config = get_config()
        self._connection_params = {
            'host': self.config['db_host'],
            'port': self.config['db_port'],
            'user': self.config['db_user'],
            'password': self.config['db_password'],
            'database': self.config['db_database']
        }
        self.connection = None
    
    def __enter__(self):
        self.connection = self.get_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.commit()
            self.connection.close()
    
    def get_connection(self) -> psycopg2.extensions.connection:
        try:
            return psycopg2.connect(**self._connection_params)
        except psycopg2.Error as e:
            raise psycopg2.Error(f"Failed to connect to database: {e}")
    
    def execute_command(self, query: str, params: Optional[tuple] = None) -> None:
        with self.connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
    
    def execute_command_batch(self, query: str, params_list: List[Optional[tuple]]) -> None:
        with self.connection.cursor() as cursor:
            for params in params_list:
                cursor.execute(query, params)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        with self.connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
    
    def execute_query_batch(self, query: str, params_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        all_results = []
        
        with self.connection.cursor() as cursor:
            for params in params_list:
                if params:
                    cursor.execute(query, tuple(params.values()) if isinstance(params, dict) else params)
                else:
                    cursor.execute(query)
                
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                all_results.append(results)
        
        return all_results
from psycopg2 import pool
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenSpendingDBService:
    """Service class for handling database operations with connection pooling"""
    
    _connection_pool = None

    @classmethod
    def initialize_pool(cls):
        """Initialize the connection pool if it hasn't been created yet"""
        if cls._connection_pool is None:
            cls._connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )

    @classmethod
    def get_connection(cls):
        """Get a connection from the pool"""
        if cls._connection_pool is None:
            cls.initialize_pool()
        return cls._connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        """Return a connection to the pool"""
        cls._connection_pool.putconn(connection)

    @classmethod
    def execute_query(cls, query: str, params: tuple = None) -> List[Dict[Any, Any]]:
        """
        Execute a SQL query and return the results as a list of dictionaries
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the SQL query
            
        Returns:
            List[Dict]: Query results where each row is a dictionary
        """
        connection = None
        try:
            connection = cls.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                # Get column names from cursor description
                columns = [desc[0] for desc in cursor.description]
                # Fetch all rows and convert to list of dictionaries
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                connection.commit()
                return results
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                cls.return_connection(connection)

    @classmethod
    def close_pool(cls):
        """Close the connection pool"""
        if cls._connection_pool is not None:
            cls._connection_pool.closeall()
            cls._connection_pool = None

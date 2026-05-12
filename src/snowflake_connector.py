"""
Snowflake Connection Module
Handles secure connection to Snowflake using environment variables
"""
import os
from typing import Optional
from dotenv import load_dotenv
from snowflake.connector import connect, SnowflakeConnection
import logging

logger = logging.getLogger(__name__)


class SnowflakeConnector:
    """Manages Snowflake database connections"""
    
    def __init__(self, config: dict):
        """
        Initialize Snowflake connector with configuration
        
        Args:
            config: Configuration dictionary containing Snowflake credentials
        """
        self.config = config
        self.connection: Optional[SnowflakeConnection] = None
        self._load_env_variables()
        
    def _load_env_variables(self):
        """Load environment variables from .env file"""
        load_dotenv()
        
        # Replace environment variable placeholders in config
        if isinstance(self.config, dict):
            self._replace_env_vars(self.config)
    
    def _replace_env_vars(self, obj):
        """Recursively replace ${VAR_NAME} with actual environment variable values"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._replace_env_vars(value)
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            var_name = obj[2:-1]
            return os.getenv(var_name, obj)
        return obj
    
    def connect(self) -> SnowflakeConnection:
        """
        Establish connection to Snowflake
        
        Returns:
            SnowflakeConnection: Active connection object
            
        Raises:
            Exception: If connection fails
        """
        try:
            if self.connection is None or not self.connection.is_closed():
                logger.info("Establishing Snowflake connection...")
                
                sf_config = self.config.get('snowflake', {})
                
                self.connection = connect(
                    account=sf_config.get('account'),
                    user=sf_config.get('user'),
                    authenticator=sf_config.get('authenticator', 'externalbrowser'),
                    role=sf_config.get('role'),
                    warehouse=sf_config.get('warehouse'),
                    database=sf_config.get('database'),
                    schema=sf_config.get('schema')
                )
                
                logger.info(f"Successfully connected to Snowflake account: {sf_config.get('account')}")
                return self.connection
                
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            raise
    
    def disconnect(self):
        """Close the Snowflake connection"""
        try:
            if self.connection and not self.connection.is_closed():
                self.connection.close()
                logger.info("Snowflake connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")
    
    def get_connection(self) -> SnowflakeConnection:
        """
        Get active connection, establishing one if needed
        
        Returns:
            SnowflakeConnection: Active connection object
        """
        if self.connection is None or self.connection.is_closed():
            return self.connect()
        return self.connection
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

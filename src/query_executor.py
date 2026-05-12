"""
Query Execution Module
Handles parallel execution of queries with logging and error handling
"""
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes SQL queries with parallel processing and comprehensive logging"""
    
    def __init__(self, snowflake_connector, max_parallel: int = 5, timeout: int = 300):
        """
        Initialize query executor
        
        Args:
            snowflake_connector: SnowflakeConnector instance
            max_parallel: Maximum number of parallel queries
            timeout: Query timeout in seconds
        """
        self.connector = snowflake_connector
        self.max_parallel = max_parallel
        self.timeout = timeout
        self.execution_results: List[Dict[str, Any]] = []
    
    def execute_query(self, query_name: str, sql: str) -> Dict[str, Any]:
        """
        Execute a single query and return results with metadata
        
        Args:
            query_name: Name/identifier for the query
            sql: SQL query string
            
        Returns:
            Dictionary containing query results and metadata
        """
        result = {
            'query_name': query_name,
            'sql': sql,
            'status': 'pending',
            'start_time': None,
            'end_time': None,
            'execution_time': None,
            'row_count': 0,
            'data': None,
            'error': None
        }
        
        try:
            logger.info(f"Executing query: {query_name}")
            result['start_time'] = datetime.now()
            
            conn = self.connector.get_connection()
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(sql)
            
            # Fetch results as DataFrame
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            result['data'] = pd.DataFrame(rows, columns=columns)
            result['row_count'] = len(result['data'])
            result['status'] = 'success'
            
            cursor.close()
            
            logger.info(f"Query '{query_name}' completed successfully. Rows: {result['row_count']}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"Query '{query_name}' failed: {str(e)}")
            
        finally:
            result['end_time'] = datetime.now()
            if result['start_time']:
                result['execution_time'] = (result['end_time'] - result['start_time']).total_seconds()
            
            self.execution_results.append(result)
        
        return result
    
    def execute_queries_parallel(self, queries: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Execute multiple queries in parallel
        
        Args:
            queries: List of query dictionaries with 'name', 'sql', 'sheet_name', 'refresh_frequency'
            
        Returns:
            List of execution results
        """
        logger.info(f"Starting parallel execution of {len(queries)} queries")
        self.execution_results = []
        
        # Filter enabled queries
        enabled_queries = [q for q in queries if q.get('enabled', True)]
        
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            # Submit all queries
            future_to_query = {
                executor.submit(
                    self.execute_query, 
                    q['name'], 
                    q['sql']
                ): q for q in enabled_queries
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    result = future.result()
                    logger.info(
                        f"Query '{query['name']}' completed: {result['status']} "
                        f"({result['execution_time']:.2f}s, {result['row_count']} rows)"
                    )
                except Exception as e:
                    logger.error(f"Query '{query['name']}' raised exception: {str(e)}")
        
        success_count = sum(1 for r in self.execution_results if r['status'] == 'success')
        logger.info(
            f"Parallel execution completed: {success_count}/{len(enabled_queries)} queries succeeded"
        )
        
        return self.execution_results
    
    def execute_queries_sequential(self, queries: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Execute multiple queries sequentially (useful for debugging)
        
        Args:
            queries: List of query dictionaries
            
        Returns:
            List of execution results
        """
        logger.info(f"Starting sequential execution of {len(queries)} queries")
        self.execution_results = []
        
        enabled_queries = [q for q in queries if q.get('enabled', True)]
        
        for query in enabled_queries:
            self.execute_query(query['name'], query['sql'])
        
        return self.execution_results
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of all query executions
        
        Returns:
            Dictionary with execution statistics
        """
        if not self.execution_results:
            return {}
        
        total = len(self.execution_results)
        success = sum(1 for r in self.execution_results if r['status'] == 'success')
        failed = total - success
        total_time = sum(r['execution_time'] or 0 for r in self.execution_results)
        total_rows = sum(r['row_count'] for r in self.execution_results)
        
        return {
            'total_queries': total,
            'successful': success,
            'failed': failed,
            'success_rate': f"{(success/total*100):.1f}%",
            'total_execution_time': f"{total_time:.2f}s",
            'total_rows': total_rows,
            'details': self.execution_results
        }

"""
Orchestrator Module
Main coordination module that ties all components together
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
import yaml
from datetime import datetime

from .snowflake_connector import SnowflakeConnector
from .query_executor import QueryExecutor
from .excel_writer import ExcelWriter
from .scheduler import JobScheduler
from .logger_setup import setup_logger

logger = logging.getLogger(__name__)


class IncentiveAutomationOrchestrator:
    """Main orchestrator for the incentive automation system"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize the orchestrator
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Setup logging
        setup_logger(self.config)
        
        # Initialize components
        self.snowflake_connector = SnowflakeConnector(self.config)
        self.query_executor = None  # Will be initialized after connection
        self.excel_writer = ExcelWriter(self.config)
        self.scheduler = JobScheduler(self.config)
        
        # State tracking
        self.last_refresh_time = None
        self.last_execution_summary = None
        
        logger.info("Incentive Automation Orchestrator initialized")
    
    def _load_config(self) -> dict:
        """
        Load configuration from YAML file
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise
    
    def _initialize_query_executor(self):
        """Initialize query executor with connection"""
        perf_config = self.config.get('performance', {})
        self.query_executor = QueryExecutor(
            self.snowflake_connector,
            max_parallel=perf_config.get('max_parallel_queries', 5),
            timeout=perf_config.get('query_timeout', 300)
        )
    
    def refresh_queries(self, frequency_filter: str = None) -> Dict[str, Any]:
        """
        Execute all queries based on their refresh frequency
        
        Args:
            frequency_filter: Optional filter for refresh frequency (manual, daily, weekly)
            
        Returns:
            Execution summary dictionary
        """
        logger.info("Starting query refresh process")
        
        queries = self.config.get('queries', [])
        
        # Filter queries by frequency if specified
        if frequency_filter:
            queries = [q for q in queries if q.get('refresh_frequency', '').lower() == frequency_filter.lower()]
            logger.info(f"Filtered to {len(queries)} queries with frequency: {frequency_filter}")
        
        # Initialize query executor
        self._initialize_query_executor()
        
        # Connect to Snowflake
        with self.snowflake_connector:
            # Execute queries in parallel
            execution_results = self.query_executor.execute_queries_parallel(queries)
        
        # Write results to Excel
        if execution_results:
            output_path = self.excel_writer.write_results(execution_results, queries)
            logger.info(f"Results written to: {output_path}")
        
        # Update state
        self.last_refresh_time = datetime.now()
        self.last_execution_summary = self.query_executor.get_execution_summary()
        
        return self.last_execution_summary
    
    def refresh_manual(self) -> Dict[str, Any]:
        """
        Manually trigger refresh of all manual queries
        
        Returns:
            Execution summary dictionary
        """
        logger.info("Manual refresh triggered")
        return self.refresh_queries(frequency_filter='manual')
    
    def refresh_all(self) -> Dict[str, Any]:
        """
        Refresh all enabled queries regardless of frequency
        
        Returns:
            Execution summary dictionary
        """
        logger.info("Full refresh triggered (all queries)")
        return self.refresh_queries(frequency_filter=None)
    
    def start_scheduler(self):
        """Start the automated scheduler"""
        logger.info("Starting scheduler")
        
        # Schedule daily jobs
        self.scheduler.schedule_daily(self.refresh_all)
        
        # Schedule weekly jobs
        self.scheduler.schedule_weekly(self.refresh_all)
        
        # Register manual job
        self.scheduler.schedule_manual(self.refresh_manual)
        
        # Start scheduler
        self.scheduler.start()
        
        logger.info(f"Scheduler started. Next run: {self.scheduler.get_next_run_time()}")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        logger.info("Stopping scheduler")
        self.scheduler.stop()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current system status
        
        Returns:
            Status dictionary
        """
        return {
            'last_refresh_time': self.last_refresh_time.isoformat() if self.last_refresh_time else None,
            'scheduler_enabled': self.scheduler.enabled,
            'scheduler_running': self.scheduler.running,
            'next_scheduled_run': self.scheduler.get_next_run_time(),
            'last_execution_summary': self.last_execution_summary,
            'scheduled_jobs': self.scheduler.get_scheduled_jobs() if self.scheduler.running else []
        }
    
    def run_once(self):
        """Execute one full refresh cycle and exit"""
        logger.info("Running single refresh cycle")
        summary = self.refresh_all()
        logger.info(f"Refresh cycle completed: {summary}")
        return summary

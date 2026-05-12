"""
Scheduler Module
Handles automated scheduling of query execution
"""
import logging
import schedule
import time
from datetime import datetime
from typing import Callable, Optional
from threading import Thread
import signal

logger = logging.getLogger(__name__)


class JobScheduler:
    """Manages scheduled execution of jobs"""
    
    def __init__(self, config: dict):
        """
        Initialize scheduler
        
        Args:
            config: Configuration dictionary with scheduler settings
        """
        self.config = config
        self.scheduler_config = config.get('scheduler', {})
        self.enabled = self.scheduler_config.get('enabled', True)
        self.timezone = self.scheduler_config.get('timezone', 'Asia/Kolkata')
        self.running = False
        self.scheduler_thread: Optional[Thread] = None
        
        if not self.enabled:
            logger.info("Scheduler is disabled in configuration")
    
    def schedule_daily(self, job_func: Callable, time_str: str = None):
        """
        Schedule a job to run daily at a specific time
        
        Args:
            job_func: Function to execute
            time_str: Time in HH:MM format (e.g., "09:00")
        """
        if not self.enabled:
            logger.warning("Scheduler is disabled, cannot schedule daily job")
            return
        
        if time_str is None:
            time_str = self.scheduler_config.get('daily_time', '09:00')
        
        schedule.every().day.at(time_str).do(job_func)
        logger.info(f"Scheduled daily job at {time_str} ({self.timezone})")
    
    def schedule_weekly(self, job_func: Callable, day: str = None, time_str: str = None):
        """
        Schedule a job to run weekly on a specific day and time
        
        Args:
            job_func: Function to execute
            day: Day of week (monday, tuesday, etc.)
            time_str: Time in HH:MM format
        """
        if not self.enabled:
            logger.warning("Scheduler is disabled, cannot schedule weekly job")
            return
        
        if day is None:
            day = self.scheduler_config.get('weekly_day', 'monday')
        if time_str is None:
            time_str = self.scheduler_config.get('weekly_time', '09:00')
        
        getattr(schedule.every(), day.lower()).at(time_str).do(job_func)
        logger.info(f"Scheduled weekly job on {day} at {time_str} ({self.timezone})")
    
    def schedule_manual(self, job_func: Callable):
        """
        Register a manual job that can be triggered on demand
        
        Args:
            job_func: Function to execute
        """
        logger.info("Registered manual job (can be triggered on demand)")
        self.manual_job = job_func
    
    def run_manual_job(self):
        """Execute the manual job immediately"""
        if hasattr(self, 'manual_job'):
            logger.info("Executing manual job")
            try:
                self.manual_job()
                logger.info("Manual job completed successfully")
            except Exception as e:
                logger.error(f"Manual job failed: {str(e)}")
        else:
            logger.warning("No manual job registered")
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop"""
        logger.info("Scheduler thread started")
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        logger.info("Scheduler thread stopped")
    
    def start(self):
        """Start the scheduler in a background thread"""
        if not self.enabled:
            logger.warning("Scheduler is disabled, not starting")
            return
        
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler started in background thread")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        logger.info("Stopping scheduler...")
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def get_next_run_time(self) -> Optional[str]:
        """
        Get the next scheduled run time
        
        Returns:
            String representation of next run time, or None if no jobs scheduled
        """
        if not self.enabled or not schedule.jobs:
            return None
        
        next_job = schedule.next_run()
        if next_job:
            return next_job.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_scheduled_jobs(self) -> list:
        """
        Get list of scheduled jobs
        
        Returns:
            List of job descriptions
        """
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                'job': str(job.job_func),
                'next_run': job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else None,
                'interval': str(job.interval)
            })
        return jobs

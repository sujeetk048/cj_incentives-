"""
Main Entry Point
Can be used to run the automation system without the web dashboard
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import IncentiveAutomationOrchestrator


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Incentive Automation System')
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--mode',
        choices=['once', 'scheduled'],
        default='once',
        help='Execution mode: once (single run) or scheduled (with scheduler)'
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = IncentiveAutomationOrchestrator(args.config)
    
    if args.mode == 'once':
        # Run once and exit
        print("Running single refresh cycle...")
        summary = orchestrator.run_once()
        print(f"\nExecution Summary:")
        print(f"  Total Queries: {summary.get('total_queries', 0)}")
        print(f"  Successful: {summary.get('successful', 0)}")
        print(f"  Failed: {summary.get('failed', 0)}")
        print(f"  Success Rate: {summary.get('success_rate', '0%')}")
        print(f"  Total Rows: {summary.get('total_rows', 0)}")
        print(f"  Total Time: {summary.get('total_execution_time', '0s')}")
    
    elif args.mode == 'scheduled':
        # Run with scheduler
        print("Starting scheduled execution...")
        orchestrator.start_scheduler()
        
        try:
            # Keep the script running
            import time
            while True:
                time.sleep(60)
                status = orchestrator.get_status()
                print(f"\nScheduler Status: Running")
                print(f"Last Refresh: {status.get('last_refresh_time', 'Never')}")
                print(f"Next Run: {status.get('next_scheduled_run', 'Unknown')}")
        except KeyboardInterrupt:
            print("\nShutting down scheduler...")
            orchestrator.stop_scheduler()


if __name__ == '__main__':
    main()

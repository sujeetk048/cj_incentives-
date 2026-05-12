# Incentive HTML Automation System

A complete, production-ready system for automating Snowflake query execution with Excel output, scheduling, and optional web dashboard.

## Features

- **Snowflake Integration**: Secure connection using environment variables
- **Parallel Query Execution**: Execute multiple queries concurrently for performance
- **Excel Output**: Professional formatting with auto-width, frozen headers, and styled headers
- **Flexible Scheduling**: Manual, Daily, or Weekly refresh frequencies
- **Error Handling**: Continues execution even if individual queries fail
- **Comprehensive Logging**: Detailed logs with rotation for query status and performance
- **Web Dashboard**: Optional Flask-based UI for monitoring and manual control
- **Config-Driven**: YAML-based configuration for easy management

## Project Structure

```
incentive_automation/
├── config.yaml              # Main configuration file
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── main.py                 # CLI entry point
├── app.py                  # Flask web dashboard
├── logs/                   # Log files (auto-created)
└── src/
    ├── __init__.py
    ├── snowflake_connector.py    # Snowflake connection management
    ├── query_executor.py         # Query execution engine
    ├── excel_writer.py           # Excel output with formatting
    ├── logger_setup.py           # Logging configuration
    ├── scheduler.py              # Job scheduling
    └── orchestrator.py           # Main orchestration logic
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Navigate to the project directory
cd incentive_automation

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your Snowflake credentials
# Never commit .env to version control!
```

Edit `.env` with your actual credentials:

```env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_email@company.com
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
```

### 3. Configure Queries

Edit `config.yaml` to add your queries:

```yaml
queries:
  - name: "Total Sales"
    sql: "SELECT * FROM sales_table WHERE date >= CURRENT_DATE - 30"
    sheet_name: "Total_Sales"
    refresh_frequency: "daily"
    enabled: true
```

**Query Configuration Fields:**
- `name`: Unique identifier for the query
- `sql`: SQL query to execute
- `sheet_name`: Excel sheet name for output
- `refresh_frequency`: One of: `manual`, `daily`, `weekly`
- `enabled`: Set to `false` to temporarily disable

### 4. Run the System

#### Option A: Single Execution (CLI)

```bash
# Run once and exit
python main.py --mode once

# Run with custom config
python main.py --config custom_config.yaml --mode once
```

#### Option B: Scheduled Execution (CLI)

```bash
# Run with scheduler (keeps running)
python main.py --mode scheduled
```

#### Option C: Web Dashboard

```bash
# Start the Flask dashboard
python app.py

# Access at http://localhost:5000
```

## Configuration Options

### Snowflake Configuration

```yaml
snowflake:
  account: ${SNOWFLAKE_ACCOUNT}
  user: ${SNOWFLAKE_USER}
  authenticator: externalbrowser  # or 'password'
  role: ${SNOWFLAKE_ROLE}
  warehouse: ${SNOWFLAKE_WAREHOUSE}
  database: ${SNOWFLAKE_DATABASE}
  schema: ${SNOWFLAKE_SCHEMA}
```

### Excel Configuration

```yaml
excel:
  output_file: "Incentive_Report.xlsx"
  overwrite: true  # true = overwrite sheets, false = append
  auto_width: true
  freeze_header: true
  header_style:
    font:
      bold: true
      color: "FFFFFF"
    fill:
      type: "solid"
      color: "4472C4"
```

### Scheduler Configuration

```yaml
scheduler:
  enabled: true
  timezone: "Asia/Kolkata"
  daily_time: "09:00"  # HH:MM format
  weekly_day: "monday"  # monday, tuesday, etc.
  weekly_time: "09:00"
```

### Performance Configuration

```yaml
performance:
  max_parallel_queries: 5
  query_timeout: 300  # seconds
```

### Logging Configuration

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  log_file: "logs/incentive_automation.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

## Web Dashboard Features

The Flask dashboard provides:

- **Real-time Status**: View last refresh time, success rate, and scheduler status
- **Manual Controls**: Trigger refreshes for all queries or manual-only queries
- **Scheduler Control**: Start/stop the automated scheduler
- **Query History**: View execution status, time, and row count for each query
- **Auto-refresh**: Status updates every 30 seconds

## Usage Examples

### Running a Single Refresh

```python
from src.orchestrator import IncentiveAutomationOrchestrator

# Initialize
orchestrator = IncentiveAutomationOrchestrator('config.yaml')

# Refresh all queries
summary = orchestrator.refresh_all()
print(f"Success rate: {summary['success_rate']}")

# Refresh only manual queries
summary = orchestrator.refresh_manual()
```

### Using the Scheduler

```python
from src.orchestrator import IncentiveAutomationOrchestrator

orchestrator = IncentiveAutomationOrchestrator('config.yaml')

# Start scheduler (runs in background)
orchestrator.start_scheduler()

# Check status
status = orchestrator.get_status()
print(f"Next run: {status['next_scheduled_run']}")

# Stop scheduler
orchestrator.stop_scheduler()
```

### Custom Query Execution

```python
from src.snowflake_connector import SnowflakeConnector
from src.query_executor import QueryExecutor

# Connect
connector = SnowflakeConnector(config)
with connector:
    executor = QueryExecutor(connector)
    
    # Execute single query
    result = executor.execute_query(
        "My Query",
        "SELECT * FROM my_table LIMIT 10"
    )
    
    print(f"Rows: {result['row_count']}")
    print(f"Data: {result['data']}")
```

## Error Handling

The system includes comprehensive error handling:

- **Query Failures**: If a query fails, the error is logged and execution continues
- **Connection Failures**: Automatic reconnection attempts
- **Excel Write Failures**: Detailed error messages with context
- **Scheduler Failures**: Graceful degradation if scheduler crashes

All errors are logged to the log file with timestamps and context.

## Logging

Logs are written to `logs/incentive_automation.log` with automatic rotation:

- **Max file size**: 10MB (configurable)
- **Backup count**: 5 files (configurable)
- **Log levels**: DEBUG, INFO, WARNING, ERROR

Log entries include:
- Timestamp
- Logger name
- Log level
- Function name and line number
- Detailed message

## Security Best Practices

1. **Never hardcode credentials**: Always use environment variables
2. **Protect .env file**: Add `.env` to `.gitignore`
3. **Use read-only roles**: Grant minimum necessary permissions
4. **Rotate credentials**: Regularly update Snowflake credentials
5. **Enable logging**: Monitor logs for suspicious activity
6. **Use HTTPS**: If deploying dashboard, use SSL/TLS

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Snowflake

**Solutions**:
- Verify credentials in `.env`
- Check network connectivity
- Ensure Snowflake account is accessible
- Try `authenticator: password` if external browser fails

### Query Timeout

**Problem**: Queries timing out

**Solutions**:
- Increase `query_timeout` in config
- Optimize SQL queries
- Check warehouse size in Snowflake
- Reduce parallel query count

### Excel Write Errors

**Problem**: Cannot write to Excel file

**Solutions**:
- Check file permissions
- Ensure file is not open in another program
- Verify output path exists
- Check disk space

### Scheduler Not Running

**Problem**: Scheduler not executing jobs

**Solutions**:
- Verify `scheduler.enabled: true` in config
- Check system time/timezone settings
- Review logs for scheduler errors
- Ensure script keeps running (not daemonized)

## Performance Optimization

1. **Parallel Execution**: Increase `max_parallel_queries` for faster execution
2. **Query Optimization**: Write efficient SQL queries
3. **Warehouse Sizing**: Use appropriate Snowflake warehouse size
4. **Batch Processing**: Group related queries
5. **Caching**: Consider caching reference data

## Deployment

### As Windows Service

Use tools like `NSSM` (Non-Sucking Service Manager) to run as a Windows service:

```bash
# Install NSSM
nssm install IncentiveAutomation "C:\path\to\python.exe" "C:\path\to\main.py" --mode scheduled
nssm start IncentiveAutomation
```

### As Linux Systemd Service

Create `/etc/systemd/system/incentive-automation.service`:

```ini
[Unit]
Description=Incentive Automation System
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/incentive_automation
ExecStart=/path/to/venv/bin/python main.py --mode scheduled
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable incentive-automation
sudo systemctl start incentive-automation
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "--mode", "scheduled"]
```

Build and run:

```bash
docker build -t incentive-automation .
docker run -d --env-file .env incentive-automation
```

## Support and Contributing

For issues, questions, or contributions, please contact the development team.

## License

[Specify your license here]

## Changelog

### Version 1.0.0
- Initial release
- Snowflake integration
- Parallel query execution
- Excel output with formatting
- Scheduler support
- Web dashboard
- Comprehensive logging
- Error handling

"""
Flask Web Dashboard
Optional UI for monitoring and manually triggering the incentive automation system
"""
from flask import Flask, render_template_string, jsonify, request
import logging
from pathlib import Path
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import IncentiveAutomationOrchestrator

logger = logging.getLogger(__name__)

app = Flask(__name__)
orchestrator = None

# HTML Template for Dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Incentive Automation Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            color: #333;
            font-size: 32px;
            font-weight: bold;
        }
        
        .stat-card.success .value {
            color: #10b981;
        }
        
        .stat-card.warning .value {
            color: #f59e0b;
        }
        
        .stat-card.info .value {
            color: #3b82f6;
        }
        
        .controls {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .controls h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 20px;
        }
        
        .button-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-success {
            background: #10b981;
            color: white;
        }
        
        .btn-warning {
            background: #f59e0b;
            color: white;
        }
        
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        
        .queries-section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .queries-section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 20px;
        }
        
        .query-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .query-table th,
        .query-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .query-table th {
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
            text-transform: uppercase;
            font-size: 12px;
        }
        
        .query-table tr:hover {
            background: #f9fafb;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-success {
            background: #d1fae5;
            color: #065f46;
        }
        
        .status-failed {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .status-pending {
            background: #fef3c7;
            color: #92400e;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        
        .alert.show {
            display: block;
        }
        
        .alert-success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #10b981;
        }
        
        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #ef4444;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Incentive Automation Dashboard</h1>
            <p>Monitor and manage automated Snowflake query execution</p>
        </div>
        
        <div id="alert" class="alert"></div>
        
        <div class="stats-grid">
            <div class="stat-card info">
                <h3>Last Refresh</h3>
                <div class="value" id="lastRefresh">Never</div>
            </div>
            <div class="stat-card success">
                <h3>Success Rate</h3>
                <div class="value" id="successRate">-</div>
            </div>
            <div class="stat-card warning">
                <h3>Total Queries</h3>
                <div class="value" id="totalQueries">-</div>
            </div>
            <div class="stat-card info">
                <h3>Scheduler Status</h3>
                <div class="value" id="schedulerStatus">-</div>
            </div>
        </div>
        
        <div class="controls">
            <h2>Controls</h2>
            <div class="button-group">
                <button class="btn-primary" onclick="refreshAll()" id="refreshBtn">
                    🔄 Refresh All Queries
                </button>
                <button class="btn-success" onclick="refreshManual()">
                    📋 Refresh Manual Queries
                </button>
                <button class="btn-warning" onclick="startScheduler()" id="startSchedulerBtn">
                    ▶️ Start Scheduler
                </button>
                <button class="btn-danger" onclick="stopScheduler()" id="stopSchedulerBtn">
                    ⏹️ Stop Scheduler
                </button>
                <button class="btn-primary" onclick="refreshStatus()">
                    📊 Refresh Status
                </button>
            </div>
        </div>
        
        <div class="queries-section">
            <h2>Query Execution History</h2>
            <table class="query-table">
                <thead>
                    <tr>
                        <th>Query Name</th>
                        <th>Status</th>
                        <th>Execution Time</th>
                        <th>Row Count</th>
                        <th>Error</th>
                    </tr>
                </thead>
                <tbody id="queryTableBody">
                    <tr>
                        <td colspan="5" style="text-align: center; color: #999;">
                            No execution data available
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Incentive Automation System v1.0 | Powered by Snowflake & Flask</p>
        </div>
    </div>
    
    <script>
        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert alert-${type} show`;
            setTimeout(() => {
                alert.classList.remove('show');
            }, 5000);
        }
        
        function setButtonLoading(btnId, loading) {
            const btn = document.getElementById(btnId);
            if (loading) {
                btn.disabled = true;
                btn.innerHTML = '<span class="loading"></span> Processing...';
            } else {
                btn.disabled = false;
                if (btnId === 'refreshBtn') {
                    btn.innerHTML = '🔄 Refresh All Queries';
                }
            }
        }
        
        async function refreshAll() {
            setButtonLoading('refreshBtn', true);
            try {
                const response = await fetch('/api/refresh/all', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                
                if (data.success) {
                    showAlert('All queries refreshed successfully!', 'success');
                } else {
                    showAlert('Refresh completed with some errors. Check details below.', 'error');
                }
                
                refreshStatus();
            } catch (error) {
                showAlert('Error: ' + error.message, 'error');
            } finally {
                setButtonLoading('refreshBtn', false);
            }
        }
        
        async function refreshManual() {
            try {
                const response = await fetch('/api/refresh/manual', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                
                if (data.success) {
                    showAlert('Manual queries refreshed successfully!', 'success');
                } else {
                    showAlert('Refresh completed with some errors.', 'error');
                }
                
                refreshStatus();
            } catch (error) {
                showAlert('Error: ' + error.message, 'error');
            }
        }
        
        async function startScheduler() {
            try {
                const response = await fetch('/api/scheduler/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                
                if (data.success) {
                    showAlert('Scheduler started successfully!', 'success');
                } else {
                    showAlert('Failed to start scheduler: ' + data.message, 'error');
                }
                
                refreshStatus();
            } catch (error) {
                showAlert('Error: ' + error.message, 'error');
            }
        }
        
        async function stopScheduler() {
            try {
                const response = await fetch('/api/scheduler/stop', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                
                if (data.success) {
                    showAlert('Scheduler stopped successfully!', 'success');
                } else {
                    showAlert('Failed to stop scheduler: ' + data.message, 'error');
                }
                
                refreshStatus();
            } catch (error) {
                showAlert('Error: ' + error.message, 'error');
            }
        }
        
        async function refreshStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update stats
                document.getElementById('lastRefresh').textContent = 
                    data.last_refresh_time ? new Date(data.last_refresh_time).toLocaleString() : 'Never';
                
                document.getElementById('successRate').textContent = 
                    data.last_execution_summary?.success_rate || '-';
                
                document.getElementById('totalQueries').textContent = 
                    data.last_execution_summary?.total_queries || '-';
                
                document.getElementById('schedulerStatus').textContent = 
                    data.scheduler_running ? 'Running' : 'Stopped';
                
                // Update query table
                const tbody = document.getElementById('queryTableBody');
                if (data.last_execution_summary?.details && data.last_execution_summary.details.length > 0) {
                    tbody.innerHTML = data.last_execution_summary.details.map(q => `
                        <tr>
                            <td>${q.query_name}</td>
                            <td><span class="status-badge status-${q.status}">${q.status}</span></td>
                            <td>${q.execution_time ? q.execution_time.toFixed(2) + 's' : '-'}</td>
                            <td>${q.row_count}</td>
                            <td>${q.error || '-'}</td>
                        </tr>
                    `).join('');
                }
                
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        }
        
        // Auto-refresh status every 30 seconds
        setInterval(refreshStatus, 30000);
        
        // Initial load
        refreshStatus();
    </script>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Render the dashboard"""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route('/api/status')
def get_status():
    """Get current system status"""
    try:
        status = orchestrator.get_status() if orchestrator else {}
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh/all', methods=['POST'])
def refresh_all():
    """Refresh all queries"""
    try:
        summary = orchestrator.refresh_all()
        success = summary.get('failed', 0) == 0
        return jsonify({'success': success, 'summary': summary})
    except Exception as e:
        logger.error(f"Error refreshing all queries: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/refresh/manual', methods=['POST'])
def refresh_manual():
    """Refresh manual queries only"""
    try:
        summary = orchestrator.refresh_manual()
        success = summary.get('failed', 0) == 0
        return jsonify({'success': success, 'summary': summary})
    except Exception as e:
        logger.error(f"Error refreshing manual queries: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the scheduler"""
    try:
        orchestrator.start_scheduler()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the scheduler"""
    try:
        orchestrator.stop_scheduler()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


def init_orchestrator(config_path='config.yaml'):
    """Initialize the orchestrator"""
    global orchestrator
    orchestrator = IncentiveAutomationOrchestrator(config_path)


def run_dashboard(host='0.0.0.0', port=5000, config_path='config.yaml'):
    """
    Run the Flask dashboard
    
    Args:
        host: Host to bind to
        port: Port to run on
        config_path: Path to configuration file
    """
    init_orchestrator(config_path)
    logger.info(f"Starting dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    run_dashboard()

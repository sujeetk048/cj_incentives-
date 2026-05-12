"""
Streamlit Web App for Snowflake Query Execution
Features:
- SQL query input with execution
- Result display as interactive table
- CSV/Excel download
- Query history
- Saved queries
- Role-based access
"""
import streamlit as st
import pandas as pd
import os
import sys
import subprocess
import re
import time
import tempfile
from datetime import datetime
from dotenv import load_dotenv
import json
from pathlib import Path
import hashlib

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Incentives",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, attractive design
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fa;
        color: #000000 !important;
        font-size: 16px;
    }
    * {
        color: #000000 !important;
    }
    /* Larger base font + spacing for readability */
    html, body, [class*="css"] { font-size: 16px; }
    p, div, span, label, .stMarkdown, .stCaption {
        font-size: 1rem;
    }
    .stCaption, .stMarkdown small, small { font-size: 0.85rem !important; }
    h1 { font-size: 2.4rem !important; }
    h2 { font-size: 1.7rem !important; }
    h3 { font-size: 1.35rem !important; }
    h4 { font-size: 1.15rem !important; }
    /* Sidebar text */
    section[data-testid='stSidebar'] * { font-size: 0.95rem; }
    section[data-testid='stSidebar'] h1,
    section[data-testid='stSidebar'] h2,
    section[data-testid='stSidebar'] h3,
    section[data-testid='stSidebar'] h4 { font-size: 1.1rem !important; }
    /* Buttons + inputs */
    .stButton>button { font-size: 1rem !important; padding: 0.55rem 1rem !important; }
    .stTextArea textarea, .stTextInput input { font-size: 1rem !important; }
    /* Tabs */
    button[data-baseweb='tab'] { font-size: 1rem !important; }
    /* DataFrames */
    div[data-testid='stDataFrame'] { font-size: 0.95rem; }
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 2rem;
        max-width: 1400px;
        margin-top: 0 !important;
    }
    /* Collapse most Streamlit chrome but KEEP the running/stop indicator visible */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 48px !important; min-height: 48px !important;
        z-index: 100 !important;
    }
    div[data-testid="stToolbar"] { display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    /* Force the sidebar expand-arrow (»») visible when sidebar is collapsed */
    div[data-testid="collapsedControl"],
    div[data-testid="stSidebarCollapsedControl"],
    button[data-testid="stSidebarCollapseButton"],
    button[kind="header"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999 !important;
    }
    /* Status widget shows the spinner + Stop button while a script/query runs */
    div[data-testid="stStatusWidget"] {
        position: fixed !important;
        top: 12px !important; right: 16px !important;
        z-index: 9999 !important;
        background: #ffffff !important;
        border-radius: 10px !important;
        padding: 6px 10px !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.12) !important;
        border: 1px solid #e5e7eb !important;
    }
    div[data-testid="stStatusWidget"] * { color: #1a1a2e !important; }
    .main > div:first-child { padding-top: 0 !important; margin-top: 0 !important; }
    section.main > div { padding-top: 0 !important; margin-top: 0 !important; }
    div[data-testid="stAppViewContainer"] > section.main { padding-top: 0 !important; }
    /* First element in main container should sit flush at top */
    .main .block-container > div:first-child { margin-top: 0 !important; padding-top: 0 !important; }
    /* Hero banner — pull it up against the top */
    .app-hero { margin-top: 0 !important; }
    /* Sidebar inner padding */
    div[data-testid="stSidebarUserContent"] { padding-top: 0.5rem !important; }
    h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    h2, h3 {
        color: #16213e;
        font-weight: 600;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        background-color: white;
        color: #1a1a2e;
    }
    .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        color: #1a1a2e;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        background-color: white;
        color: #1a1a2e;
    }
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        color: #1a1a2e;
    }
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    .metric-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    /* Radio button labels */
    .stRadio label, .stRadio div[role="radiogroup"] label p {
        color: #1a1a2e !important;
    }
    /* General label fix for all widgets */
    label, .stTextArea label, .stTextInput label, .stSelectbox label,
    .stFileUploader label, .stRadio label {
        color: #1a1a2e !important;
    }
    /* Sidebar text */
    .stSidebar, .stSidebar p, .stSidebar div, .stSidebar label {
        color: #1a1a2e !important;
    }
    /* General paragraph and div text */
    p, div {
        color: #1a1a2e;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)

# Configuration
HISTORY_FILE = "query_history.json"
SAVED_QUERIES_FILE = "saved_queries.json"
USERS_FILE = "users.json"
SHEETS_ROOT = Path(__file__).parent / "sheets_data"
SHEETS_ROOT.mkdir(exist_ok=True)


def safe_name(name: str) -> str:
    """Strip characters unsafe for filenames."""
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in (name or ""))


def get_user_sheets_dir(username: str) -> Path:
    """Per-user folder. Each user's data is fully isolated."""
    folder = safe_name(username) if username else "_anonymous"
    user_dir = SHEETS_ROOT / folder
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_active_username() -> str:
    """Whose workspace is active. Admin can override via 'view_as_user'."""
    if st.session_state.get('view_as_user') and st.session_state.get('role') == 'admin':
        return st.session_state['view_as_user']
    return st.session_state.get('username') or ''


def _sf_profile_path(username: str) -> Path:
    return get_user_sheets_dir(username) / "sf_profile.json"


def load_sf_profile(username: str) -> dict:
    """Load this user's Snowflake credentials (email/role/warehouse). Empty dict if not set yet."""
    path = _sf_profile_path(username)
    if not path.exists():
        return {}
    try:
        with open(path, 'r') as f:
            data = json.load(f) or {}
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def save_sf_profile(username: str, profile: dict):
    """Persist Snowflake credentials for this user."""
    with open(_sf_profile_path(username), 'w') as f:
        json.dump(profile, f, indent=2)


def sf_env_for_user(username: str) -> dict:
    """Build the env dict (SF_USER / SF_ROLE / etc.) to pass to sf_runner.py for this user."""
    profile = load_sf_profile(username)
    env = os.environ.copy()
    env['SF_USER']      = profile.get('sf_user', '')
    env['SF_ROLE']      = profile.get('sf_role', '')
    env['SF_ACCOUNT']   = profile.get('sf_account',   os.getenv('SNOWFLAKE_ACCOUNT',   'CQ31887-CARS24CSPL'))
    env['SF_WAREHOUSE'] = profile.get('sf_warehouse', os.getenv('SNOWFLAKE_WAREHOUSE', ''))
    return env


def render_sf_setup_form(username: str):
    """First-time Snowflake setup form. Returns True if profile was saved this call."""
    st.markdown("### ❄️ Snowflake — first-time setup")
    st.caption(
        "Enter your Snowflake account details. These are saved to your workspace and "
        "reused every time you log in. You can change them later from the sidebar."
    )
    existing = load_sf_profile(username)
    sf_user = st.text_input(
        "Snowflake email",
        value=existing.get('sf_user', ''),
        placeholder="firstname.lastname@cars24.com",
        key="sfsetup_user",
    )
    sf_role = st.text_input(
        "Snowflake role",
        value=existing.get('sf_role', ''),
        placeholder="e.g. SUJEET_KUMAR_RL",
        key="sfsetup_role",
        help="Your Snowflake role (case-sensitive). Leave blank to use your default role.",
    )
    sf_warehouse = st.text_input(
        "Snowflake warehouse (optional)",
        value=existing.get('sf_warehouse', ''),
        placeholder="e.g. COMPUTE_WH",
        key="sfsetup_warehouse",
    )
    sf_account = st.text_input(
        "Snowflake account",
        value=existing.get('sf_account', 'CQ31887-CARS24CSPL'),
        key="sfsetup_account",
    )

    if st.button("💾 Save & Continue", type="primary", use_container_width=True, key="sfsetup_save"):
        sf_user_clean = (sf_user or '').strip()
        if not sf_user_clean or '@' not in sf_user_clean:
            st.error("Please enter a valid Snowflake email.")
            return False
        save_sf_profile(username, {
            'sf_user':      sf_user_clean,
            'sf_role':      (sf_role or '').strip(),
            'sf_account':   (sf_account or 'CQ31887-CARS24CSPL').strip(),
            'sf_warehouse': (sf_warehouse or '').strip(),
        })
        st.success("Saved. The next query will use your Snowflake account.")
        st.rerun()
    return False


def list_workspace_users():
    """List all usernames that have a saved workspace on disk (for admin view)."""
    users = []
    if SHEETS_ROOT.exists():
        for child in SHEETS_ROOT.iterdir():
            if child.is_dir() and (child / "sheets_meta.json").exists():
                users.append(child.name)
    return sorted(users)


SCHEME_CSV = Path(__file__).parent / "scheme.csv"


def load_scheme_sheet():
    """Load the read-only scheme tab from scheme.csv (shipped with the app)."""
    if not SCHEME_CSV.exists():
        return None
    try:
        df = pd.read_csv(SCHEME_CSV)
    except Exception:
        return None
    return {
        'name': 'Scheme',
        'type': 'scheme',  # special read-only type
        'query': None,
        'df': df,
        'error': None,
        'status': 'success',
    }


def ensure_scheme_first(sheets):
    """Inject the Scheme tab at index 0 if missing, refresh its DataFrame each load."""
    scheme = load_scheme_sheet()
    if scheme is None:
        return sheets
    sheets = [s for s in sheets if s.get('type') != 'scheme' and s.get('name') != 'Scheme']
    return [scheme] + sheets


def save_sheets(sheets):
    """Persist sheet metadata + dataframes under the active user's folder.
    The built-in Scheme tab is excluded from per-user persistence.
    """
    user_dir = get_user_sheets_dir(get_active_username())
    meta_file = user_dir / "sheets_meta.json"
    meta = []
    for s in sheets:
        if s.get('type') == 'scheme':
            continue  # never persist the built-in scheme tab
        fname = safe_name(s['name'])
        entry = {
            'name': s['name'],
            'type': s.get('type', 'sql'),
            'query': s.get('query'),
            'status': s['status'],
            'error': s.get('error'),
            'file': None,
        }
        if s['df'] is not None and len(s['df']) > 0:
            csv_path = user_dir / f"{fname}.csv"
            try:
                s['df'].to_csv(csv_path, index=False)
                entry['file'] = fname + '.csv'
            except Exception:
                pass
        meta.append(entry)
    with open(meta_file, 'w') as f:
        json.dump(meta, f, indent=2)


def load_sheets():
    """Load sheets for the active user."""
    user_dir = get_user_sheets_dir(get_active_username())
    meta_file = user_dir / "sheets_meta.json"
    if not meta_file.exists():
        return ensure_scheme_first([])
    try:
        with open(meta_file, 'r') as f:
            meta = json.load(f)
        sheets = []
        for entry in meta:
            df = None
            if entry.get('file'):
                csv_path = user_dir / entry['file']
                if csv_path.exists():
                    try:
                        df = pd.read_csv(csv_path)
                    except Exception:
                        df = None
            sheets.append({
                'name': entry['name'],
                'type': entry.get('type', 'sql'),
                'query': entry.get('query'),
                'status': entry['status'] if df is not None else ('pending' if entry.get('type') == 'sql' else entry['status']),
                'error': entry.get('error'),
                'df': df,
            })
        return ensure_scheme_first(sheets)
    except Exception:
        return ensure_scheme_first([])


# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'saved_queries' not in st.session_state:
    st.session_state.saved_queries = []
if 'batch_queries' not in st.session_state:
    st.session_state.batch_queries = []
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = None
if 'sheets' not in st.session_state:
    st.session_state.sheets = []  # populated on login per-user
if 'show_builder' not in st.session_state:
    st.session_state.show_builder = False
if 'builder_joins' not in st.session_state:
    st.session_state.builder_joins = []
if 'builder_measures' not in st.session_state:
    st.session_state.builder_measures = []
if 'view_as_user' not in st.session_state:
    st.session_state.view_as_user = None
if 'workspace_loaded_for' not in st.session_state:
    st.session_state.workspace_loaded_for = None
if 'running_query' not in st.session_state:
    st.session_state.running_query = None  # dict: {sheet_idx, pid, result_path, err_path}
if 'kpi_auto_refresh' not in st.session_state:
    st.session_state.kpi_auto_refresh = True


def smart_fix_kpi_error(sql_query, error_msg, all_sheets):
    """Analyze a DuckDB error and suggest a fixed query.
    Returns (suggestion_text, fixed_query_or_None).
    """
    import difflib

    # Build catalog of available tables and columns
    table_cols = {}
    for s in all_sheets:
        if s.get('type') == 'kpi' or s.get('df') is None:
            continue
        table_cols[s['name']] = list(s['df'].columns)

    # ── Pattern 1: Ambiguous column reference ────────────────────────────
    m = re.search(r'Ambiguous reference to column name\s+"([^"]+)"', error_msg)
    if m:
        col = m.group(1)
        # Find which tables contain this column
        owners = [t for t, cols in table_cols.items() if col in cols]
        if owners:
            chosen = owners[0]
            # Qualify the bare column with the first table found
            fixed = re.sub(rf'(?<![\w."]){re.escape(col)}(?!\w)', f'{chosen}.{col}', sql_query)
            return (
                f"`{col}` exists in: **{', '.join(owners)}**.\n\n"
                f"Suggested: qualify it as `{chosen}.{col}`",
                fixed
            )
        return (f"Column `{col}` is ambiguous but not found in any registered table.", None)

    # ── Pattern 2: Table does not exist ──────────────────────────────────
    m = re.search(r'Table with name (\w+) does not exist', error_msg)
    if not m:
        m = re.search(r'Catalog Error.*?["\']?(\w+)["\']?\s+does not exist', error_msg)
    if m:
        bad = m.group(1)
        candidates = list(table_cols.keys())
        matches = difflib.get_close_matches(bad, candidates, n=3, cutoff=0.4)
        if matches:
            fixed = re.sub(rf'\b{re.escape(bad)}\b', matches[0], sql_query)
            return (
                f"Table `{bad}` not found. Closest match: **{matches[0]}**\n\n"
                f"Other options: {', '.join(matches[1:]) or '—'}\n\n"
                f"Available: {', '.join(candidates)}",
                fixed
            )
        return (f"Table `{bad}` not found. Available: {', '.join(candidates) or 'none'}", None)

    # ── Pattern 3: Column not found ──────────────────────────────────────
    m = re.search(r'(?:Referenced column|Binder Error.*column)\s+["\']?(\w+)["\']?\s+not found', error_msg)
    if m:
        bad = m.group(1)
        all_cols = {c: t for t, cols in table_cols.items() for c in cols}
        matches = difflib.get_close_matches(bad, list(all_cols.keys()), n=3, cutoff=0.5)
        if matches:
            best = matches[0]
            owner = all_cols[best]
            fixed = re.sub(rf'\b{re.escape(bad)}\b', best, sql_query)
            return (
                f"Column `{bad}` not found. Closest match: **{best}** (in `{owner}`)\n\n"
                f"Other options: {', '.join(matches[1:]) or '—'}",
                fixed
            )
        return (f"Column `{bad}` not found in any table.", None)

    return (None, None)


def execute_kpi(sql_query, all_sheets):
    """Execute SQL against loaded DataFrames using DuckDB.
    Each sheet becomes a virtual table. Registered with original name + lowercase + sanitized.
    """
    if not DUCKDB_AVAILABLE:
        return None, "duckdb is not installed. Run: pip install duckdb"

    if not sql_query.strip():
        return None, "Empty query"

    try:
        con = duckdb.connect(":memory:")
        registered = []
        for s in all_sheets:
            if s.get('df') is None:
                continue
            # Skip the currently-running KPI itself? No — allow self-reference too;
            # DuckDB will error cleanly if there's a true conflict.
            df = s['df']
            original = s['name']
            # Register under multiple name variants so users can reference flexibly
            variants = {original, original.lower(), original.replace(' ', '_'),
                        original.replace(' ', '_').lower(),
                        re.sub(r'[^A-Za-z0-9_]', '_', original)}
            for name in variants:
                if not name:
                    continue
                try:
                    con.register(name, df)
                except Exception:
                    pass
            registered.append(original)

        if not registered:
            return None, "No data sheets to reference. Add and run some data sheets first."

        try:
            result = con.execute(sql_query).fetchdf()
            con.close()
            return result, None
        except Exception as e:
            con.close()
            err_msg = str(e)
            # Catalog error → show available tables
            if "Catalog Error" in err_msg or "does not exist" in err_msg.lower():
                tables_list = ", ".join(f'"{r}"' for r in registered)
                return None, f"{err_msg}\n\nAvailable tables: {tables_list}"
            return None, err_msg
    except Exception as e:
        return None, str(e)


def auto_refresh_kpis(reason=""):
    """Recalculate every KPI sheet and persist. Shows a toast with the count.
    Skips silently if auto-refresh is off in session state."""
    if not st.session_state.get('kpi_auto_refresh', True):
        return 0
    count = 0
    for sheet in st.session_state.get('sheets', []):
        if sheet.get('type') != 'kpi' or not sheet.get('query'):
            continue
        df, err = execute_kpi(sheet['query'], st.session_state.sheets)
        sheet['df']     = df
        sheet['error']  = err
        sheet['status'] = 'success' if df is not None else 'failed'
        count += 1
    if count:
        save_sheets(st.session_state.sheets)
        try:
            st.toast(f"🔄 Auto-refreshed {count} KPI sheet(s) {reason}".strip(), icon="⚡")
        except Exception:
            pass
    return count


def execute_query(query):
    """Blocking execute — used for Run All / Refresh All flows."""
    try:
        runner = Path(__file__).parent / "sf_runner.py"
        env = sf_env_for_user(get_active_username())
        proc = subprocess.run(
            [sys.executable, str(runner)],
            input=query,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        stdout = proc.stdout.strip()
        if proc.returncode != 0:
            return None, proc.stderr.strip() or "Unknown error"
        if not stdout:
            return None, proc.stderr.strip() or "No output from query runner"
        data = json.loads(stdout)
        if isinstance(data, dict) and "__error__" in data:
            return None, data["__error__"]
        return pd.DataFrame(data), None
    except subprocess.TimeoutExpired:
        return None, "Query timed out after 5 minutes"
    except Exception as e:
        return None, str(e)


def start_query_async(query, sheet_idx):
    """Start a query in background. Returns (pid, result_path, err_path)."""
    tmp = Path(tempfile.gettempdir())
    result_path = str(tmp / f"sf_result_{sheet_idx}.json")
    err_path    = str(tmp / f"sf_err_{sheet_idx}.txt")
    runner = Path(__file__).parent / "sf_runner.py"
    env = sf_env_for_user(get_active_username())
    out_f = open(result_path, 'w')
    err_f = open(err_path, 'w')
    proc = subprocess.Popen(
        [sys.executable, str(runner)],
        stdin=subprocess.PIPE,
        stdout=out_f,
        stderr=err_f,
        text=True,
        env=env,
    )
    proc.stdin.write(query)
    proc.stdin.close()
    out_f.close()
    err_f.close()
    return proc.pid, result_path, err_path


def is_pid_running(pid):
    """Cross-platform check whether a PID is still alive."""
    try:
        if sys.platform == 'win32':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                capture_output=True, text=True
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def stop_query_process(pid):
    """Kill a running query subprocess."""
    try:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/PID', str(pid), '/T'],
                           capture_output=True)
        else:
            os.kill(pid, 9)
    except Exception:
        pass


def read_async_result(result_path, err_path):
    """Read result written by sf_runner. Returns (df, error)."""
    try:
        content = Path(result_path).read_text().strip()
        if not content:
            err = Path(err_path).read_text().strip()
            return None, err or "No output from query runner"
        data = json.loads(content)
        if isinstance(data, dict) and "__error__" in data:
            return None, data["__error__"]
        return pd.DataFrame(data), None
    except Exception as e:
        return None, str(e)


def convert_datetime_to_naive(df):
    """Convert timezone-aware datetime columns to timezone-naive for Excel export"""
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)
    return df


def load_users():
    """Load users from file"""
    if Path(USERS_FILE).exists():
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {
        'admin': {'password': 'admin123', 'role': 'admin'},
        'user': {'password': 'user123', 'role': 'user'}
    }


def authenticate(username, password):
    """Authenticate user"""
    users = load_users()
    if username in users and users[username]['password'] == password:
        return True, users[username]['role']
    return False, None


def load_query_history():
    """Load query history from file"""
    if Path(HISTORY_FILE).exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []


def save_query_history(history):
    """Save query history to file"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)


def load_saved_queries():
    """Load saved queries from file"""
    if Path(SAVED_QUERIES_FILE).exists():
        with open(SAVED_QUERIES_FILE, 'r') as f:
            return json.load(f)
    return []


def save_saved_queries(queries):
    """Save saved queries to file"""
    with open(SAVED_QUERIES_FILE, 'w') as f:
        json.dump(queries, f)


def login_page():
    """Premium login screen with animated gradient + glass-morphism card."""
    st.markdown("""
    <style>
      /* Hide sidebar + Streamlit chrome */
      section[data-testid="stSidebar"] { display: none; }
      header[data-testid="stHeader"] { display: none !important; }
      div[data-testid="stToolbar"], div[data-testid="stDecoration"] { display: none !important; }

      /* Animated gradient background */
      .stApp {
          background: linear-gradient(135deg,
              #0a0e1f 0%, #0d1235 25%, #1a1a4d 50%, #2a1f5e 75%, #1a1a4d 100%) !important;
          background-size: 400% 400% !important;
          animation: gradientShift 15s ease infinite;
      }
      html, body { background: #0a0e1f !important; }
      @keyframes gradientShift {
          0%   { background-position: 0% 50%; }
          50%  { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
      }

      /* Decorative blurred orbs floating in the background */
      .stApp::before, .stApp::after {
          content: '';
          position: fixed;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.5;
          pointer-events: none;
          z-index: 0;
      }
      .stApp::before {
          width: 400px; height: 400px;
          background: #3245FF;
          top: -100px; left: -100px;
          animation: float1 12s ease-in-out infinite;
      }
      .stApp::after {
          width: 350px; height: 350px;
          background: #06b6d4;
          bottom: -80px; right: -80px;
          animation: float2 14s ease-in-out infinite;
      }
      @keyframes float1 {
          0%,100% { transform: translate(0,0); }
          50%     { transform: translate(60px, 80px); }
      }
      @keyframes float2 {
          0%,100% { transform: translate(0,0); }
          50%     { transform: translate(-60px,-80px); }
      }

      .main .block-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding-top: 0 !important;
          max-width: 100% !important;
          position: relative;
          z-index: 1;
      }

      .stApp, .stApp * { color: #e5e7eb !important; }

      /* Glass-morphism card */
      .login-card {
          background: rgba(22, 26, 35, 0.7);
          backdrop-filter: blur(18px);
          -webkit-backdrop-filter: blur(18px);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 16px;
          padding: 1.6rem 1.5rem 0.6rem 1.5rem;
          width: 320px;
          box-shadow: 0 20px 60px rgba(0,0,0,0.55),
                      inset 0 1px 0 rgba(255,255,255,0.06);
          margin: 0 auto 0.5rem auto;
          animation: cardIn 0.6s ease-out;
      }
      @keyframes cardIn {
          from { opacity:0; transform: translateY(20px); }
          to   { opacity:1; transform: translateY(0); }
      }

      /* Animated logo badge */
      .login-logo {
          display: flex; justify-content: center;
          margin-bottom: 0.8rem;
      }
      .login-logo .badge {
          width: 56px; height: 56px;
          border-radius: 14px;
          background: linear-gradient(135deg, #3245FF 0%, #06b6d4 100%);
          display: flex; align-items: center; justify-content: center;
          box-shadow: 0 6px 22px rgba(50,69,255,0.55),
                      inset 0 1px 0 rgba(255,255,255,0.25);
          animation: pulse 2.5s ease-in-out infinite;
      }
      @keyframes pulse {
          0%,100% { box-shadow: 0 6px 22px rgba(50,69,255,0.55), inset 0 1px 0 rgba(255,255,255,0.25); }
          50%     { box-shadow: 0 6px 30px rgba(6,182,212,0.65),  inset 0 1px 0 rgba(255,255,255,0.25); }
      }

      .login-card h1 {
          color: #ffffff !important;
          text-align: center;
          font-size: 1.25rem;
          font-weight: 700;
          margin: 0 0 0.15rem 0;
          letter-spacing: -0.01em;
      }
      .login-card .sub {
          text-align: center;
          font-size: 0.78rem;
          color: #94a3b8 !important;
          margin: 0;
      }

      .login-footer {
          width: 320px;
          margin: 0 auto;
          font-size: 0.7rem;
          color: #6b7280 !important;
          text-align: center;
          line-height: 1.5;
          position: relative; z-index: 1;
      }
      .login-footer * { color: #6b7280 !important; }

      /* Inputs — modern dark with glow on focus */
      .stTextInput > div > div {
          background: rgba(15,19,32,0.85) !important;
          border: 1px solid rgba(255,255,255,0.08) !important;
          border-radius: 8px !important;
          transition: all 0.18s ease !important;
      }
      .stTextInput > div > div:hover {
          border-color: rgba(255,255,255,0.18) !important;
      }
      .stTextInput > div > div:focus-within {
          border-color: #3245FF !important;
          box-shadow: 0 0 0 3px rgba(50,69,255,0.25) !important;
          background: rgba(15,19,32,1) !important;
      }
      .stTextInput > div > div > input {
          background: transparent !important;
          border: none !important;
          color: #ffffff !important;
          padding: 0.5rem 0.8rem !important;
          font-size: 0.9rem !important;
          height: 38px !important;
          caret-color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
      }
      .stTextInput > div > div > input::placeholder {
          color: #6b7280 !important;
          -webkit-text-fill-color: #6b7280 !important;
      }
      /* Show-password eye icon toggle — keep it visible on dark bg */
      .stTextInput button[aria-label],
      .stTextInput button svg {
          color: #94a3b8 !important;
          fill: #94a3b8 !important;
      }
      .stTextInput button:hover svg {
          color: #ffffff !important;
          fill: #ffffff !important;
      }
      /* Autofill background fix (Chrome) */
      .stTextInput input:-webkit-autofill {
          -webkit-box-shadow: 0 0 0 30px rgba(15,19,32,1) inset !important;
          -webkit-text-fill-color: #ffffff !important;
          caret-color: #ffffff !important;
      }
      .stTextInput label, .stTextInput label * {
          color: #cbd5e1 !important;
          font-size: 0.8rem !important;
          font-weight: 600 !important;
          letter-spacing: 0.01em;
      }
      .stTextInput { margin-bottom: 0.25rem !important; }
      div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }

      /* Sign-in button — gradient with shine on hover */
      .stButton > button {
          background: linear-gradient(135deg, #3245FF 0%, #1d4ed8 100%) !important;
          color: #ffffff !important;
          border: none !important;
          border-radius: 10px !important;
          padding: 0.55rem 1rem !important;
          font-weight: 700 !important;
          font-size: 0.95rem !important;
          height: 40px !important;
          margin-top: 0.5rem;
          letter-spacing: 0.02em;
          box-shadow: 0 6px 18px rgba(50,69,255,0.45);
          transition: all 0.18s ease !important;
          position: relative;
          overflow: hidden;
      }
      .stButton > button * { color: #ffffff !important; }
      .stButton > button:hover {
          transform: translateY(-2px) !important;
          box-shadow: 0 10px 24px rgba(50,69,255,0.6);
          background: linear-gradient(135deg, #4456ff 0%, #2563eb 100%) !important;
      }
      .stButton > button:active {
          transform: translateY(0) !important;
      }
    </style>
    """, unsafe_allow_html=True)

    # Inline SVG of the Cars24 broken-circle mark
    logo_svg = (
        "<svg viewBox='0 0 100 100' width='32' height='32' xmlns='http://www.w3.org/2000/svg'>"
        "<path d='M70 30 A28 28 0 1 0 70 70' stroke='#ffffff' stroke-width='12' "
        "stroke-linecap='round' fill='none'/></svg>"
    )

    left, mid, right = st.columns([3, 2, 3])
    with mid:
        st.markdown(f"""
        <div class='login-card'>
            <div class='login-logo'><div class='badge'>{logo_svg}</div></div>
            <h1>Welcome back</h1>
            <p class='sub'>Sign in to the Incentive Dashboard</p>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", key="login_username", placeholder="your.name")
        password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")

        sign_in = st.button("Sign in →", use_container_width=True, type="primary", key="login_btn")

        st.markdown(
            "<div class='login-footer'>Cars24 · CJ Incentive Dashboard<br/>"
            "Need access? Contact your admin.</div>",
            unsafe_allow_html=True,
        )

        if sign_in:
            success, role = authenticate(username, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = role
                st.session_state.view_as_user = None
                st.session_state.query_history = load_query_history()
                st.session_state.saved_queries = load_saved_queries()
                st.session_state.sheets = load_sheets()
                st.session_state.workspace_loaded_for = username
                st.session_state.builder_joins = []
                st.session_state.builder_measures = []
                st.session_state.show_builder = False
                st.rerun()
            else:
                st.error("Invalid username or password")


@st.cache_data(show_spinner=False)
def download_excel_bytes(_sheets_key: str, sheets: dict) -> bytes:
    """Build Excel bytes — cached by sheets_key so it only rebuilds when data changes."""
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        for sheet_name, df in sheets.items():
            convert_datetime_to_naive(df.copy()).to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def df_to_csv(_df_key: str, df: pd.DataFrame) -> str:
    """Cache CSV conversion so it doesn't recompute on every rerun."""
    return df.to_csv(index=False)


def sheets_cache_key(sheets):
    """Stable key based on sheet names + row counts — cheap to compute."""
    return "|".join(f"{s['name']}:{len(s['df']) if s['df'] is not None else 0}" for s in sheets)


def build_sql_from_visual(base_table, joins, group_by, measures, where_clause=""):
    """Generate DuckDB SQL from visual builder selections."""
    if not base_table:
        return ""

    # SELECT clause
    select_parts = list(group_by) if group_by else []
    for m in measures:
        kind = m.get('kind', 'agg')
        alias = m.get('alias', 'metric')
        if kind == 'agg':
            col = m.get('column', '*')
            func = m.get('func', 'COUNT')
            if col == '*' and func.upper() != 'COUNT':
                col = group_by[0] if group_by else '1'
            select_parts.append(f"{func}({col}) AS {alias}")
        elif kind == 'slab':
            col = m.get('column', '')
            slabs = m.get('slabs', [])  # list of {min, max, value}
            else_val = m.get('else', 0)
            cases = []
            for sl in slabs:
                lo = sl.get('min', '')
                hi = sl.get('max', '')
                val = sl.get('value', 0)
                conditions = []
                if lo != '' and lo is not None:
                    conditions.append(f"{col} >= {lo}")
                if hi != '' and hi is not None:
                    conditions.append(f"{col} <= {hi}")
                if conditions:
                    cases.append(f"WHEN {' AND '.join(conditions)} THEN {val}")
            if cases:
                outer = m.get('outer_func', 'SUM')
                expr = f"CASE {' '.join(cases)} ELSE {else_val} END"
                select_parts.append(f"{outer}({expr}) AS {alias}")
        elif kind == 'flat':
            col = m.get('column', '*')
            per_unit = m.get('per_unit', 0)
            select_parts.append(f"COUNT({col}) * {per_unit} AS {alias}")

    if not select_parts:
        select_parts = ['*']

    sql = f"SELECT {', '.join(select_parts)}\nFROM {base_table}"
    for j in joins:
        right = j.get('right_table')
        left_key = j.get('left_key')
        right_key = j.get('right_key')
        join_type = j.get('join_type', 'LEFT JOIN')
        if right and left_key and right_key:
            if left_key == right_key:
                sql += f"\n{join_type} {right} USING({left_key})"
            else:
                sql += f"\n{join_type} {right} ON {base_table}.{left_key} = {right}.{right_key}"

    if where_clause.strip():
        sql += f"\nWHERE {where_clause.strip()}"

    if group_by:
        sql += f"\nGROUP BY {', '.join(group_by)}"

    return sql


def render_visual_builder():
    """Form-based UI to compose joins + measures and save as a KPI sheet."""
    # Include KPI sheets too so users can join existing KPIs into new ones
    available = [
        s for s in st.session_state.sheets
        if s.get('df') is not None and s.get('type') != 'scheme'
    ]
    if not available:
        st.warning("Visual Builder needs at least one data sheet. Add an SQL or CSV sheet first.")
        if st.button("Close Builder"):
            st.session_state.show_builder = False
            st.rerun()
        return

    # Map: table_name -> list of columns
    table_cols = {s['name']: list(s['df'].columns) for s in available}
    table_names = list(table_cols.keys())

    st.markdown("""
    <div class='vb-hero' style='background: linear-gradient(135deg, #00c4cc 0%, #3245FF 100%);
                padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 1rem;'>
        <h2 style='color:#ffffff !important; margin:0; font-size:1.3rem;'>Visual Builder — Join Tables & Build Measures</h2>
        <p style='color:rgba(255,255,255,0.9) !important; margin:0.3rem 0 0 0; font-size:0.85rem;'>
            Pick tables → add joins → define measures → save as KPI sheet
        </p>
    </div>
    <style>
      .vb-hero, .vb-hero * { color: #ffffff !important; }
      .vb-hero p { color: rgba(255,255,255,0.9) !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Step 1: Base table ──────────────────────────────────────────────────
    st.markdown("##### 1. Base Table")
    base_table = st.selectbox("Select the main table", options=table_names, key="vb_base")
    base_cols = table_cols.get(base_table, [])

    # ── Step 2: Joins ───────────────────────────────────────────────────────
    st.markdown("##### 2. Joined Tables (optional)")
    if st.button("➕ Add Join", key="vb_add_join"):
        st.session_state.builder_joins.append({
            'right_table': table_names[0] if table_names else '',
            'join_type': 'LEFT JOIN',
            'left_key': '',
            'right_key': '',
        })
        st.rerun()

    for ji, j in enumerate(st.session_state.builder_joins):
        c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 1.5, 1.5, 0.5])
        with c1:
            j['join_type'] = st.selectbox(
                "Type", ["LEFT JOIN", "INNER JOIN", "RIGHT JOIN", "FULL JOIN"],
                index=["LEFT JOIN", "INNER JOIN", "RIGHT JOIN", "FULL JOIN"].index(j.get('join_type', 'LEFT JOIN')),
                key=f"vb_jtype_{ji}"
            )
        with c2:
            j['right_table'] = st.selectbox(
                "Right Table", options=table_names,
                index=table_names.index(j['right_table']) if j.get('right_table') in table_names else 0,
                key=f"vb_jright_{ji}"
            )
        with c3:
            j['left_key'] = st.selectbox(
                f"Key on {base_table}", options=[''] + base_cols,
                index=([''] + base_cols).index(j['left_key']) if j.get('left_key') in [''] + base_cols else 0,
                key=f"vb_lkey_{ji}"
            )
        with c4:
            r_cols = table_cols.get(j['right_table'], [])
            j['right_key'] = st.selectbox(
                f"Key on {j['right_table']}", options=[''] + r_cols,
                index=([''] + r_cols).index(j['right_key']) if j.get('right_key') in [''] + r_cols else 0,
                key=f"vb_rkey_{ji}"
            )
        with c5:
            st.write("")
            if st.button("🗑️", key=f"vb_jdel_{ji}"):
                st.session_state.builder_joins.pop(ji)
                st.rerun()

    # ── Step 3: Group By ────────────────────────────────────────────────────
    st.markdown("##### 3. Group By Columns")
    # Build a flat list of all columns available (base + joined)
    all_cols = list(base_cols)
    for j in st.session_state.builder_joins:
        all_cols.extend(table_cols.get(j['right_table'], []))
    all_cols = list(dict.fromkeys(all_cols))  # dedupe preserving order

    group_by = st.multiselect("Pick one or more columns to group by", options=all_cols, key="vb_groupby")

    # ── Step 4: Measures ────────────────────────────────────────────────────
    st.markdown("##### 4. Measures")
    if st.button("➕ Add Measure", key="vb_add_measure"):
        st.session_state.builder_measures.append({
            'kind': 'agg', 'func': 'COUNT', 'column': '*', 'alias': 'count_metric',
        })
        st.rerun()

    for mi, m in enumerate(st.session_state.builder_measures):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 0.5])
            with c1:
                m['kind'] = st.selectbox(
                    "Type",
                    options=['agg', 'flat', 'slab'],
                    format_func=lambda x: {'agg': 'Aggregation', 'flat': 'Per-Unit (flat ₹)', 'slab': 'Slab / Tier'}[x],
                    index=['agg', 'flat', 'slab'].index(m.get('kind', 'agg')),
                    key=f"vb_mkind_{mi}"
                )
            with c2:
                m['alias'] = st.text_input("Name (alias)", value=m.get('alias', f'metric_{mi}'), key=f"vb_malias_{mi}")
            with c3:
                st.write("")
                if st.button("🗑️", key=f"vb_mdel_{mi}"):
                    st.session_state.builder_measures.pop(mi)
                    st.rerun()

            if m['kind'] == 'agg':
                c1, c2 = st.columns(2)
                with c1:
                    m['func'] = st.selectbox(
                        "Function",
                        ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT DISTINCT'],
                        index=['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT DISTINCT'].index(m.get('func', 'COUNT')),
                        key=f"vb_mfunc_{mi}"
                    )
                with c2:
                    m['column'] = st.selectbox(
                        "Column",
                        ['*'] + all_cols,
                        index=(['*'] + all_cols).index(m['column']) if m.get('column') in ['*'] + all_cols else 0,
                        key=f"vb_mcol_{mi}"
                    )

            elif m['kind'] == 'flat':
                c1, c2 = st.columns(2)
                with c1:
                    m['column'] = st.selectbox(
                        "Count what",
                        ['*'] + all_cols,
                        index=(['*'] + all_cols).index(m['column']) if m.get('column') in ['*'] + all_cols else 0,
                        key=f"vb_mflatcol_{mi}"
                    )
                with c2:
                    m['per_unit'] = st.number_input("₹ per unit", value=float(m.get('per_unit', 0)), key=f"vb_mflat_{mi}")

            elif m['kind'] == 'slab':
                c1, c2, c3 = st.columns(3)
                with c1:
                    m['column'] = st.selectbox(
                        "Slab on column",
                        all_cols if all_cols else [''],
                        index=all_cols.index(m['column']) if m.get('column') in all_cols else 0,
                        key=f"vb_mslabcol_{mi}"
                    )
                with c2:
                    m['outer_func'] = st.selectbox(
                        "Aggregator", ['SUM', 'AVG', 'MAX', 'MIN'],
                        index=['SUM', 'AVG', 'MAX', 'MIN'].index(m.get('outer_func', 'SUM')),
                        key=f"vb_mslabouter_{mi}"
                    )
                with c3:
                    m['else'] = st.number_input("Else value", value=float(m.get('else', 0)), key=f"vb_mslabelse_{mi}")

                slabs = m.setdefault('slabs', [])
                if st.button("➕ Slab Row", key=f"vb_addslab_{mi}"):
                    slabs.append({'min': 0, 'max': 0, 'value': 0})
                    st.rerun()
                for si, sl in enumerate(slabs):
                    sc1, sc2, sc3, sc4 = st.columns([1, 1, 1, 0.3])
                    with sc1:
                        sl['min'] = st.number_input("Min", value=float(sl.get('min', 0)), key=f"vb_slabmin_{mi}_{si}")
                    with sc2:
                        sl['max'] = st.number_input("Max", value=float(sl.get('max', 0)), key=f"vb_slabmax_{mi}_{si}")
                    with sc3:
                        sl['value'] = st.number_input("Value", value=float(sl.get('value', 0)), key=f"vb_slabval_{mi}_{si}")
                    with sc4:
                        st.write("")
                        if st.button("🗑️", key=f"vb_slabdel_{mi}_{si}"):
                            slabs.pop(si)
                            st.rerun()

    # ── Step 5: Where (optional) ────────────────────────────────────────────
    st.markdown("##### 5. Filter (optional)")
    where_clause = st.text_input("WHERE clause (raw SQL)", placeholder="e.g. region = 'T7'", key="vb_where")

    # ── Preview & Save ──────────────────────────────────────────────────────
    st.markdown("##### 6. Preview & Save")
    sql_preview = build_sql_from_visual(
        base_table,
        st.session_state.builder_joins,
        group_by,
        st.session_state.builder_measures,
        where_clause
    )
    st.code(sql_preview, language='sql')

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        new_name = st.text_input("KPI Sheet Name", placeholder="e.g. Productivity_Incentive", key="vb_save_name")
    with col_b:
        if st.button("Save as KPI Sheet", type="primary", use_container_width=True):
            if not new_name or not sql_preview.strip():
                st.error("Enter a sheet name and have a non-empty query")
            else:
                existing = [s['name'] for s in st.session_state.sheets]
                if new_name in existing:
                    st.error("Sheet name already exists")
                else:
                    with st.spinner("Calculating KPI..."):
                        df, err = execute_kpi(sql_preview, st.session_state.sheets)
                    st.session_state.sheets.append({
                        'name': new_name,
                        'type': 'kpi',
                        'query': sql_preview,
                        'df': df,
                        'error': err,
                        'status': 'success' if df is not None else 'failed',
                    })
                    save_sheets(st.session_state.sheets)
                    st.session_state.builder_joins = []
                    st.session_state.builder_measures = []
                    if df is not None:
                        st.success(f"KPI sheet '{new_name}' created and calculated")
                    else:
                        st.warning(f"KPI sheet '{new_name}' saved but calculation failed: {err}")
                    st.rerun()
    with col_c:
        if st.button("Close Builder", use_container_width=True):
            st.session_state.show_builder = False
            st.rerun()


def main_app():
    """Main application — Home page shows all data sheet by sheet"""

    # ── First-time Snowflake setup gate — only runs for non-admin users
    # who haven't entered their Snowflake email yet.
    _active_user = get_active_username()
    _sf_profile  = load_sf_profile(_active_user)
    if not _sf_profile.get('sf_user'):
        render_sf_setup_form(_active_user)
        return

    st.markdown(
        """
        <style>
            /* ── Interactive polish for the main app ───────────────────── */
            .stApp { background: linear-gradient(180deg, #f5f7fa 0%, #eef1f8 100%) !important; }

            /* Sidebar: clean panel — native collapse arrow works */
            section[data-testid='stSidebar'] {
                background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
                box-shadow: 4px 0 20px rgba(15,23,42,0.04) !important;
                border-right: 1px solid #e5e7eb !important;
            }

            /* Metric cards — glass + lift on hover */
            .stApp div[style*='background:#ffffff'][style*='border-left'] {
                transition: transform 0.18s ease, box-shadow 0.18s ease !important;
                cursor: default;
            }
            .stApp div[style*='background:#ffffff'][style*='border-left']:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 10px 24px rgba(0,0,0,0.10) !important;
            }

            /* Buttons everywhere — smooth lift + shadow on hover */
            .stButton > button {
                transition: all 0.16s ease !important;
                border-radius: 8px !important;
                border: 1px solid #e5e7eb !important;
                background: #ffffff !important;
                color: #1a1a2e !important;
                font-weight: 500 !important;
            }
            .stButton > button p,
            .stButton > button span,
            .stButton > button div {
                color: #1a1a2e !important;
            }
            .stDownloadButton > button,
            .stDownloadButton > button p,
            .stDownloadButton > button span {
                color: #1a1a2e !important;
            }
            .stButton > button:hover:not(:disabled) {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 16px rgba(0,0,0,0.10) !important;
                border-color: #cbd5e1 !important;
                background: #ffffff !important;
            }
            .stButton > button:active:not(:disabled) {
                transform: translateY(0) !important;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
            }
            .stButton > button:disabled {
                opacity: 0.45 !important;
                cursor: not-allowed !important;
            }
            /* Primary buttons — brand gradient */
            .stButton > button[kind='primary'] {
                background: linear-gradient(135deg, #3245FF 0%, #1d4ed8 100%) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 4px 14px rgba(50,69,255,0.35) !important;
            }
            .stButton > button[kind='primary'] * { color: #ffffff !important; }
            .stButton > button[kind='primary']:hover:not(:disabled) {
                box-shadow: 0 8px 22px rgba(50,69,255,0.5) !important;
                background: linear-gradient(135deg, #4456ff 0%, #2563eb 100%) !important;
            }
            /* Download buttons share the lift behavior */
            .stDownloadButton > button {
                transition: all 0.16s ease !important;
                border-radius: 8px !important;
                background: #ffffff !important;
                border: 1px solid #e5e7eb !important;
            }
            .stDownloadButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 16px rgba(0,0,0,0.10) !important;
            }

            /* Inputs — soft focus ring */
            .stTextInput input, .stTextArea textarea, .stNumberInput input,
            .stSelectbox div[data-baseweb='select'] > div {
                transition: all 0.16s ease !important;
                border-radius: 8px !important;
            }
            .stTextInput input:focus, .stTextArea textarea:focus,
            .stNumberInput input:focus {
                border-color: #3245FF !important;
                box-shadow: 0 0 0 3px rgba(50,69,255,0.18) !important;
            }

            /* Expanders — softer borders + hover state */
            div[data-testid='stExpander'] {
                border: 1px solid #e5e7eb !important;
                border-radius: 10px !important;
                transition: border-color 0.16s ease, box-shadow 0.16s ease;
                background: #ffffff;
            }
            div[data-testid='stExpander']:hover {
                border-color: #cbd5e1 !important;
                box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            }
            details[open] > summary {
                color: #1d4ed8 !important;
            }

            /* DataFrames — rounded + shadow */
            div[data-testid='stDataFrame'] {
                border-radius: 10px !important;
                overflow: hidden;
                box-shadow: 0 4px 14px rgba(0,0,0,0.06);
                border: 1px solid #e5e7eb;
            }

            /* Smooth fade-in for newly rendered tab content */
            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(8px); }
                to   { opacity: 1; transform: translateY(0); }
            }
            div[data-baseweb='tab-panel'] {
                animation: fadeUp 0.25s ease;
            }

            /* Sidebar non-primary buttons — slight color */
            section[data-testid='stSidebar'] .stButton > button:not([kind="primary"]) {
                background: #ffffff !important;
                color: #1a1a2e !important;
                border: 1px solid #e5e7eb !important;
            }
            section[data-testid='stSidebar'] .stButton > button:not([kind="primary"]):hover:not(:disabled) {
                background: #f8fafc !important;
            }
            /* Sidebar primary button — keep brand gradient */
            section[data-testid='stSidebar'] .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #3245FF 0%, #1d4ed8 100%) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 4px 14px rgba(50,69,255,0.35) !important;
            }
            section[data-testid='stSidebar'] .stButton > button[kind="primary"] *,
            .stButton > button[kind="primary"] * {
                color: #ffffff !important;
            }

            /* Dividers — subtler */
            hr { border-color: #e5e7eb !important; opacity: 0.6; }

            /* Subtle decorative orb behind hero banner */
            .app-hero { position: relative; overflow: hidden; }
            .app-hero::before {
                content: '';
                position: absolute;
                width: 320px; height: 320px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(6,182,212,0.45) 0%, transparent 70%);
                top: -120px; right: -80px;
                pointer-events: none;
                animation: orbFloat 9s ease-in-out infinite;
            }
            @keyframes orbFloat {
                0%,100% { transform: translate(0,0); }
                50%     { transform: translate(-30px, 30px); }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        active = get_active_username()

        if active != st.session_state.username:
            st.info(f"Viewing workspace: **{active}**")

        # Safety: if session is showing stale sheets from previous user (rare race), reload
        if st.session_state.workspace_loaded_for != active and st.session_state.username:
            st.session_state.sheets = load_sheets()
            st.session_state.workspace_loaded_for = active

        # ── Add a new sheet ───────────────────────────────────────────────
        # Clear input widgets if a previous successful Add Sheet flagged it
        if st.session_state.pop('reset_add_inputs', False):
            for _k in ['new_sheet_name', 'new_query_input', 'kpi_query_input',
                       'csv_upload', 'excel_sheet_select']:
                if _k in st.session_state:
                    del st.session_state[_k]

        st.markdown("#### Add Sheet")
        _MODE_OPTIONS = [
            ("SQL Query",        "🟦 SQL Query"),
            ("Upload CSV",       "🟩 Upload CSV"),
            ("KPI / Calculation","🟧 KPI / Calculation"),
            ("Visual Builder",   "🟪 Visual Builder"),
        ]
        _mode_keys   = [k for k, _ in _MODE_OPTIONS]
        _mode_labels = {k: lbl for k, lbl in _MODE_OPTIONS}
        add_mode = st.radio(
            "Source",
            _mode_keys,
            format_func=lambda k: _mode_labels[k],
            horizontal=True,
            key="add_mode"
        )

        new_sheet_name = st.text_input("Sheet Name", placeholder="e.g. Sales_Data", key="new_sheet_name")

        if add_mode == "SQL Query":
            new_query = st.text_area("SQL Query", height=120, placeholder="SELECT * FROM ...", key="new_query_input")
            if st.button("Add Sheet", type="primary", use_container_width=True):
                if new_sheet_name and new_query:
                    existing = [s['name'] for s in st.session_state.sheets]
                    if new_sheet_name in existing:
                        st.error("Sheet name already exists")
                    else:
                        st.session_state.sheets.append({
                            'name': new_sheet_name,
                            'type': 'sql',
                            'query': new_query,
                            'df': None,
                            'error': None,
                            'status': 'pending'
                        })
                        save_sheets(st.session_state.sheets)
                        st.session_state.reset_add_inputs = True
                        st.rerun()
                else:
                    st.error("Enter both sheet name and query")

        elif add_mode == "Upload CSV":  # Upload File
            uploaded = st.file_uploader(
                "Upload CSV or Excel",
                type=['csv', 'xlsx', 'xls'],
                key="csv_upload"
            )

            # For Excel: show sheet selector
            excel_sheets_available = []
            selected_excel_sheets = []
            if uploaded and uploaded.name.endswith(('.xlsx', '.xls')):
                try:
                    xl = pd.ExcelFile(uploaded)
                    excel_sheets_available = xl.sheet_names
                    if len(excel_sheets_available) > 1:
                        selected_excel_sheets = st.multiselect(
                            "Select sheets to import",
                            options=excel_sheets_available,
                            default=excel_sheets_available,
                            key="excel_sheet_select"
                        )
                    else:
                        selected_excel_sheets = excel_sheets_available
                except Exception as e:
                    st.error(f"Could not read Excel file: {e}")

            if st.button("Add Sheet", type="primary", use_container_width=True):
                if not uploaded:
                    st.error("Upload a file first")
                else:
                    try:
                        existing = [s['name'] for s in st.session_state.sheets]
                        added = 0

                        if uploaded.name.endswith('.csv'):
                            # CSV — use Sheet Name field as tab name
                            tab_name = new_sheet_name or Path(uploaded.name).stem
                            if tab_name in existing:
                                st.error(f"Sheet '{tab_name}' already exists")
                            else:
                                df = pd.read_csv(uploaded)
                                st.session_state.sheets.append({
                                    'name': tab_name, 'type': 'csv',
                                    'query': None, 'df': df,
                                    'error': None, 'status': 'success'
                                })
                                added += 1

                        else:
                            # Excel — one tab per selected sheet
                            uploaded.seek(0)
                            xl = pd.ExcelFile(uploaded)
                            sheets_to_load = selected_excel_sheets or xl.sheet_names
                            for sheet_name in sheets_to_load:
                                tab_name = sheet_name
                                # Prefix with Sheet Name field if provided and multiple sheets
                                if new_sheet_name and len(sheets_to_load) > 1:
                                    tab_name = f"{new_sheet_name}_{sheet_name}"
                                elif new_sheet_name and len(sheets_to_load) == 1:
                                    tab_name = new_sheet_name
                                if tab_name in existing:
                                    st.warning(f"Skipped '{tab_name}' — already exists")
                                    continue
                                df = xl.parse(sheet_name)
                                st.session_state.sheets.append({
                                    'name': tab_name, 'type': 'csv',
                                    'query': None, 'df': df,
                                    'error': None, 'status': 'success'
                                })
                                existing.append(tab_name)
                                added += 1

                        if added:
                            save_sheets(st.session_state.sheets)
                            auto_refresh_kpis(reason=f"after uploading {added} sheet(s)")
                            st.session_state.reset_add_inputs = True
                            st.rerun()

                    except Exception as e:
                        st.error(f"Failed to read file: {e}")

        elif add_mode == "KPI / Calculation":
            available = [s['name'] for s in st.session_state.sheets if s.get('df') is not None and s.get('type') != 'kpi']
            if available:
                st.caption("Available tables: " + ", ".join(f"`{n}`" for n in available))
            else:
                st.caption("Add data sheets first — they become tables you can query.")

            kpi_query = st.text_area(
                "DuckDB SQL",
                height=180,
                placeholder=(
                    "SELECT inspector, COUNT(*) AS inspections,\n"
                    "       SUM(CASE WHEN rating>=4 THEN 100 ELSE 50 END) AS incentive\n"
                    "FROM Inspections JOIN Feedback USING(appointment_id)\n"
                    "GROUP BY inspector"
                ),
                key="kpi_query_input",
                help="Reference any tab as a table. Wrap names with spaces in double quotes."
            )

            if st.button("Add KPI Sheet", type="primary", use_container_width=True):
                if not new_sheet_name or not kpi_query:
                    st.error("Enter both sheet name and KPI query")
                else:
                    existing = [s['name'] for s in st.session_state.sheets]
                    if new_sheet_name in existing:
                        st.error("Sheet name already exists")
                    else:
                        # Auto-calculate immediately
                        with st.spinner("Calculating KPI..."):
                            df, err = execute_kpi(kpi_query, st.session_state.sheets)
                        st.session_state.sheets.append({
                            'name': new_sheet_name,
                            'type': 'kpi',
                            'query': kpi_query,
                            'df': df,
                            'error': err,
                            'status': 'success' if df is not None else 'failed',
                        })
                        save_sheets(st.session_state.sheets)
                        st.session_state.reset_add_inputs = True
                        st.rerun()

        else:  # Visual Builder
            st.caption("Use the **Visual Builder** panel on the main page to build joins + measures.")
            if st.button("Open Visual Builder", type="primary", use_container_width=True):
                st.session_state.show_builder = True
                st.rerun()

        st.divider()

        # ── Run All / Refresh All ─────────────────────────────────────────
        if st.session_state.get('sheets'):
            sql_sheets = [s for s in st.session_state.sheets if s.get('type') == 'sql']

            if sql_sheets and st.button("Run All Queries", type="primary", use_container_width=True):
                total = len(sql_sheets)
                progress_bar = st.progress(0, text="Starting...")
                status_box = st.empty()
                for idx, sheet in enumerate(sql_sheets):
                    status_box.info(f"Running {idx + 1} of {total}: **{sheet['name']}**")
                    progress_bar.progress((idx) / total, text=f"{idx + 1}/{total} — {sheet['name']}")
                    df, err = execute_query(sheet['query'])
                    sheet['df'] = df
                    sheet['error'] = err
                    sheet['status'] = 'success' if df is not None else 'failed'
                progress_bar.progress(1.0, text="All queries complete")
                status_box.success(f"Done — {total} queries executed")
                save_sheets(st.session_state.sheets)
                auto_refresh_kpis(reason="after Run All Queries")
                st.rerun()

            if st.button("Refresh All Sheets", use_container_width=True):
                for sheet in st.session_state.sheets:
                    if sheet.get('type') == 'csv':
                        continue
                    if sheet.get('type') == 'kpi':
                        continue  # handle KPI sheets after, so they see fresh data
                    with st.spinner(f"Running {sheet['name']}..."):
                        df, err = execute_query(sheet['query'])
                        sheet['df'] = df
                        sheet['error'] = err
                        sheet['status'] = 'success' if df is not None else 'failed'
                # Now recalculate all KPI sheets with fresh data
                for sheet in st.session_state.sheets:
                    if sheet.get('type') == 'kpi':
                        df, err = execute_kpi(sheet['query'], st.session_state.sheets)
                        sheet['df'] = df
                        sheet['error'] = err
                        sheet['status'] = 'success' if df is not None else 'failed'
                save_sheets(st.session_state.sheets)
                st.rerun()

            # Recalculate KPI sheets only + auto-refresh toggle
            kpi_sheets_exist = any(s.get('type') == 'kpi' for s in st.session_state.sheets)
            if kpi_sheets_exist:
                if st.button("Recalculate KPIs", use_container_width=True):
                    for sheet in st.session_state.sheets:
                        if sheet.get('type') == 'kpi':
                            df, err = execute_kpi(sheet['query'], st.session_state.sheets)
                            sheet['df'] = df
                            sheet['error'] = err
                            sheet['status'] = 'success' if df is not None else 'failed'
                    save_sheets(st.session_state.sheets)
                    st.rerun()
                # Auto-refresh toggle: when ON, KPIs auto-recalc after any Query/CSV data change
                st.session_state.kpi_auto_refresh = st.checkbox(
                    "Auto-refresh KPIs on data change",
                    value=st.session_state.get('kpi_auto_refresh', True),
                    key="kpi_auto_refresh_toggle",
                    help="When ON, every KPI sheet recalculates automatically after a Query runs or a CSV uploads."
                )

            # ── Download all as one Excel ─────────────────────────────────
            success_sheets = {s['name']: s['df'] for s in st.session_state.sheets if s['status'] == 'success' and s['df'] is not None}
            if success_sheets:
                all_key = sheets_cache_key(st.session_state.sheets)
                st.download_button(
                    label="Download All (Excel)",
                    data=download_excel_bytes(all_key, success_sheets),
                    file_name="incentives_all_sheets.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            # ── Remove All Sheets (with confirmation) ─────────────────────
            if not st.session_state.get('confirm_remove_all'):
                if st.button("🗑️ Remove All Sheets", use_container_width=True):
                    st.session_state.confirm_remove_all = True
                    st.rerun()
            else:
                st.warning(f"⚠️ Delete ALL {len(st.session_state.sheets)} sheets? This cannot be undone.")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("✅ Yes, Delete", type="primary", use_container_width=True, key="confirm_yes_remove"):
                        # Wipe on-disk files for the active user
                        try:
                            user_dir = get_user_sheets_dir(get_active_username())
                            for f in user_dir.glob("*.csv"):
                                try:
                                    f.unlink()
                                except Exception:
                                    pass
                            meta = user_dir / "sheets_meta.json"
                            if meta.exists():
                                meta.unlink()
                        except Exception:
                            pass
                        # Reset in-memory and re-inject the Scheme tab
                        st.session_state.sheets = ensure_scheme_first([])
                        st.session_state.builder_joins = []
                        st.session_state.builder_measures = []
                        st.session_state.show_builder = False
                        st.session_state.confirm_remove_all = False
                        st.success("All user sheets removed (Scheme tab preserved)")
                        st.rerun()
                with cc2:
                    if st.button("❌ Cancel", use_container_width=True, key="confirm_no_remove"):
                        st.session_state.confirm_remove_all = False
                        st.rerun()

        st.divider()

        # ── Admin: switch workspace ──────────────────────────────────────────
        if st.session_state.role == 'admin':
            workspace_users = list_workspace_users()
            options = ["(My workspace)"] + [u for u in workspace_users if u != safe_name(st.session_state.username)]
            current = "(My workspace)" if not st.session_state.view_as_user else st.session_state.view_as_user
            if current not in options:
                current = "(My workspace)"
            picked = st.selectbox(
                "Admin: View workspace",
                options=options,
                index=options.index(current),
                key="admin_view_pick"
            )
            new_view = None if picked == "(My workspace)" else picked
            if new_view != st.session_state.view_as_user:
                st.session_state.view_as_user = new_view
                st.session_state.sheets = load_sheets()
                st.session_state.builder_joins = []
                st.session_state.builder_measures = []
                st.session_state.show_builder = False
                st.rerun()

        # ── Account info ─────────────────────────────────────────────────────
        role_display = st.session_state.role or ''
        st.caption(f"App role: {role_display}")

        # ── Snowflake account — per user, editable ─────────────────────────
        _active_user_sb = get_active_username()
        _sb_profile = load_sf_profile(_active_user_sb)
        with st.expander("❄️ Snowflake account", expanded=False):
            st.caption(f"**Email:** {_sb_profile.get('sf_user', '—')}")
            st.caption(f"**Role:** {_sb_profile.get('sf_role', '—')}")
            st.caption(f"**Warehouse:** {_sb_profile.get('sf_warehouse') or '(default)'}")
            st.caption(f"**Account:** {_sb_profile.get('sf_account', '—')}")
            new_email = st.text_input("Change email", value=_sb_profile.get('sf_user', ''),
                                      key="sb_sf_email")
            new_role  = st.text_input("Change role",  value=_sb_profile.get('sf_role', ''),
                                      key="sb_sf_role")
            new_wh    = st.text_input("Change warehouse", value=_sb_profile.get('sf_warehouse', ''),
                                      key="sb_sf_wh")
            if st.button("💾 Save Snowflake settings", use_container_width=True, key="sb_sf_save"):
                save_sf_profile(_active_user_sb, {
                    'sf_user':      (new_email or '').strip(),
                    'sf_role':      (new_role or '').strip(),
                    'sf_account':   _sb_profile.get('sf_account', 'CQ31887-CARS24CSPL'),
                    'sf_warehouse': (new_wh or '').strip(),
                })
                st.success("Saved. Next query will use the updated settings.")
                st.rerun()

        # ── User info (at bottom) ────────────────────────────────────────────
        st.markdown(f"**User:** {st.session_state.username}")

        if st.button("Logout", use_container_width=True):
            # Clear ALL per-user state on logout
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.view_as_user = None
            st.session_state.sheets = []
            st.session_state.query_history = []
            st.session_state.saved_queries = []
            st.session_state.builder_joins = []
            st.session_state.builder_measures = []
            st.session_state.show_builder = False
            st.session_state.workspace_loaded_for = None
            st.rerun()

    # ── Header ───────────────────────────────────────────────────────────────
    # Inline SVG of the Cars24 mark (broken-circle "C" + Cars24 wordmark)
    cars24_svg = """
    <svg viewBox='0 0 512 512' width='110' height='110' xmlns='http://www.w3.org/2000/svg'>
        <rect width='512' height='512' rx='96' fill='#3245FF'/>
        <path d='M340 158 A116 116 0 1 0 340 354' stroke='#ffffff'
              stroke-width='62' stroke-linecap='round' fill='none'/>
        <text x='256' y='430' fill='#ffffff' font-size='86' font-weight='800'
              font-family='Inter,Segoe UI,Arial,sans-serif' text-anchor='middle'>Cars24</text>
    </svg>
    """
    st.markdown(f"""
    <div class='app-hero' style='background: linear-gradient(135deg, #0D1235 0%, #3245FF 100%);
                padding: 2rem 2.5rem; border-radius: 18px; margin-bottom: 1rem;
                box-shadow: 0 8px 28px rgba(50,69,255,0.22);
                display:flex; align-items:center; gap:1.5rem;'>
        <div style='flex-shrink:0; background:#ffffff; border-radius:20px; padding:0.4rem;
                    box-shadow:0 4px 16px rgba(0,0,0,0.18);'>{cars24_svg}</div>
        <div style='flex:1;'>
            <h1 class='hero-title' style='color:#ffffff !important; margin:0; font-size:4.5rem; font-weight:900;
                       letter-spacing:-0.03em; line-height:1.0;
                       text-shadow: 0 2px 12px rgba(0,0,0,0.25);'>Incentives — Raw Data</h1>
            <p class='hero-sub' style='color:#ffffff !important; margin:0.8rem 0 0 0;
                      font-size:1.25rem; font-weight:500; opacity:0.95;'>
                CJ Incentive Dashboard · All query results displayed sheet by sheet
            </p>
        </div>
    </div>
    <style>
      .app-hero, .app-hero * {{ color: #ffffff !important; }}
      .app-hero .hero-title {{ color: #ffffff !important; font-size: 4.5rem !important; font-weight: 900 !important; }}
      .app-hero .hero-sub  {{ color: #ffffff !important; }}
    </style>
    """, unsafe_allow_html=True)

    # ── Visual Builder panel ─────────────────────────────────────────────────
    if st.session_state.get('show_builder'):
        render_visual_builder()
        st.divider()

    # ── Sheet tabs ────────────────────────────────────────────────────────────
    if not st.session_state.get('sheets'):
        st.info("No sheets yet. Use the sidebar to add a sheet name + SQL query, then click **Add Sheet**.")
        return

    # ── (A) Dashboard metric cards — bifurcated by sheet type ─────────────
    sheets_all = st.session_state.sheets
    sheets_user = [s for s in sheets_all if s.get('type') != 'scheme']

    def _stats(filtered):
        return {
            'total':   len(filtered),
            'success': sum(1 for s in filtered if s['status'] == 'success'),
            'failed':  sum(1 for s in filtered if s['status'] == 'failed'),
            'running': sum(1 for s in filtered if s['status'] == 'running'),
        }

    stats_all    = _stats(sheets_user)
    stats_query  = _stats([s for s in sheets_user if s.get('type') == 'sql'])
    stats_manual = _stats([s for s in sheets_user if s.get('type') == 'csv'])
    stats_kpi    = _stats([s for s in sheets_user if s.get('type') == 'kpi'])

    # CJ Level — derive from session-state stored result (if user has merged)
    cjl_merged = st.session_state.get('cjl_merged_df')
    cj_total = int(len(cjl_merged)) if cjl_merged is not None else 0
    stats_cj = {
        'total':   cj_total,
        'success': cj_total if cj_total else 0,
        'failed':  0,
        'running': 0,
    }

    def _stat_card(title, icon, color, stats):
        return (
            f"<div style='background:#ffffff;border-top:4px solid {color};"
            f"border-radius:10px;padding:0.65rem 0.85rem;"
            f"box-shadow:0 2px 6px rgba(0,0,0,0.06);height:100%;'>"
            f"<div style='font-size:0.7rem;font-weight:700;color:{color};"
            f"text-transform:uppercase;letter-spacing:0.04em;margin-bottom:0.4rem;'>"
            f"{icon} {title}</div>"
            f"<div style='display:flex;justify-content:space-between;font-size:0.78rem;"
            f"color:#374151;line-height:1.5;'>"
            f"<span>Total</span><b style='color:#1a1a2e;'>{stats['total']}</b></div>"
            f"<div style='display:flex;justify-content:space-between;font-size:0.78rem;"
            f"color:#374151;line-height:1.5;'>"
            f"<span>✅ Success</span><b style='color:#16a34a;'>{stats['success']}</b></div>"
            f"</div>"
        )

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.markdown(_stat_card("Sheets",   "📊", "#2563eb", stats_all),    unsafe_allow_html=True)
    with m2: st.markdown(_stat_card("Query",    "🟦", "#3245FF", stats_query),  unsafe_allow_html=True)
    with m3: st.markdown(_stat_card("Manual",   "🟩", "#16a34a", stats_manual), unsafe_allow_html=True)
    with m4: st.markdown(_stat_card("KPIs",     "🟧", "#d97706", stats_kpi),    unsafe_allow_html=True)
    with m5: st.markdown(_stat_card("CJ Level", "👤", "#7c3aed", stats_cj),     unsafe_allow_html=True)
    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    # ── (B) Tab styling — dashboard-inspired (dark nav top tabs, lighter sub-tabs) ──
    st.markdown("""
    <style>
      /* Top-level tab list — dark navy bar */
      div[data-testid='stTabs'] > div:first-child div[data-baseweb='tab-list'] {
          background: linear-gradient(180deg, #0d1235 0%, #131a45 100%) !important;
          padding: 0.4rem 0.5rem 0 0.5rem !important;
          border-radius: 12px 12px 0 0 !important;
          gap: 0.25rem !important;
          border-bottom: none !important;
      }
      div[data-testid='stTabs'] > div:first-child button[data-baseweb='tab'] {
          background: transparent !important;
          color: #94a3b8 !important;
          border-radius: 8px 8px 0 0 !important;
          padding: 0.7rem 1.2rem !important;
          font-weight: 600 !important;
          font-size: 1rem !important;
          transition: all 0.18s ease;
          border-bottom: 3px solid transparent !important;
      }
      div[data-testid='stTabs'] > div:first-child button[data-baseweb='tab'] * { color: #94a3b8 !important; }
      div[data-testid='stTabs'] > div:first-child button[data-baseweb='tab']:hover {
          background: rgba(56,189,248,0.08) !important;
          color: #e2e8f0 !important;
      }
      div[data-testid='stTabs'] > div:first-child button[data-baseweb='tab']:hover * { color: #e2e8f0 !important; }
      div[data-testid='stTabs'] > div:first-child button[data-baseweb='tab'][aria-selected='true'] {
          background: rgba(56,189,248,0.12) !important;
          color: #ffffff !important;
          border-bottom: 3px solid #38bdf8 !important;
          font-weight: 700 !important;
          box-shadow: 0 -2px 0 rgba(56,189,248,0.0);
      }
      div[data-testid='stTabs'] > div:first-child button[data-baseweb='tab'][aria-selected='true'] * {
          color: #ffffff !important;
      }
      /* Sub-tabs (nested) — lighter card style with cyan accent */
      div[data-baseweb='tab-list'] {
          gap: 0.25rem !important;
          border-bottom: 2px solid #e5e7eb !important;
      }
      button[data-baseweb='tab'] {
          background: transparent !important;
          border-radius: 8px 8px 0 0 !important;
          padding: 0.55rem 1rem !important;
          font-weight: 500 !important;
          transition: background 0.15s ease;
      }
      button[data-baseweb='tab']:hover { background: #f3f4f6 !important; }
      button[data-baseweb='tab'][aria-selected='true'] {
          background: #ffffff !important;
          border-bottom: 3px solid #06b6d4 !important;
          font-weight: 700 !important;
          color: #0f172a !important;
      }
      /* Tab panel below the dark bar — connect visually */
      div[data-testid='stTabs'] > div:first-child div[data-baseweb='tab-panel'] {
          background: #ffffff;
          border-radius: 0 0 12px 12px;
          padding: 1rem 1.25rem;
          box-shadow: 0 4px 16px rgba(13,18,53,0.08);
          margin-bottom: 1rem;
      }
    </style>
    """, unsafe_allow_html=True)

    # Type → icon for tab labels
    TYPE_ICON = {'scheme': '📋', 'sql': '🟦', 'csv': '🟩', 'kpi': '🟧'}
    # Type → label + color for in-tab badge
    TYPE_BADGE = {
        'scheme': ('SCHEME',  '#7c3aed'),  # purple
        'sql':    ('QUERY',   '#2563eb'),  # blue
        'csv':    ('MANUAL',  '#16a34a'),  # green
        'kpi':    ('KPI',     '#ea580c'),  # orange
    }

    def _label(s):
        icon = TYPE_ICON.get(s.get('type', 'sql'), '⬜')
        if s.get('type') == 'scheme':
            return f"{icon} {s['name']} ({len(s['df'])} rows)" if s['df'] is not None else f"{icon} {s['name']}"
        # Status only shown when not success (success is the default — no clutter)
        if s['status'] == 'success' and s['df'] is not None:
            return f"{icon} {s['name']} ({len(s['df'])} rows)"
        suffix = '🔴 error' if s['status'] == 'failed' else '🟡 pending'
        return f"{icon} {s['name']} · {suffix}"

    # ── Vertical group nav (left rail) + horizontal sub-tabs (main area) ──
    GROUPS = [
        ('📋 Scheme',   'scheme', '#6b7280'),
        ('🟦 Queries',  'sql',    '#3245FF'),
        ('🟩 Manual',   'csv',    '#16a34a'),
        ('🟧 KPIs',     'kpi',    '#d97706'),
        ('👤 CJ Level', 'cjl',    '#7c3aed'),
    ]
    group_indices = {
        gtype: [idx for idx, s in enumerate(st.session_state.sheets) if s.get('type') == gtype]
        for _, gtype, _ in GROUPS if gtype != 'cjl'
    }

    # Active group state — default to first group with content
    if 'active_group' not in st.session_state:
        st.session_state.active_group = 'scheme'

    # Two-column layout: compact left rail + wide main area
    left_rail, main_area = st.columns([1, 9], gap="small")

    flat_iter = []

    with left_rail:
        st.markdown("""
        <style>
            /* Compact left-rail group buttons — extra small */
            div[data-testid="column"]:nth-of-type(1) .stButton > button {
                text-align: center !important;
                justify-content: center !important;
                padding: 0.15rem 0.3rem !important;
                font-size: 0.68rem !important;
                font-weight: 500 !important;
                margin-bottom: 0.12rem !important;
                min-height: 0 !important;
                height: 1.9rem !important;
                line-height: 1 !important;
                border-radius: 5px !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # Each group: full label (emoji + name) + count
        for label, gtype, color in GROUPS:
            count = len(group_indices.get(gtype, [])) if gtype != 'cjl' else 0
            full_label = f"{label} ({count})" if gtype != 'cjl' else label
            is_active = st.session_state.active_group == gtype
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                full_label,
                key=f"navrail_{gtype}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.active_group = gtype
                st.rerun()

    with main_area:
        active = st.session_state.active_group

        if active == 'cjl':
            render_cj_level(st.session_state.sheets)
        else:
            indices = group_indices.get(active, [])
            if not indices:
                group_name = next((lbl for lbl, gt, _ in GROUPS if gt == active), active)
                st.info(f"No sheets in **{group_name}** yet. Add one from the sidebar.")
            else:
                sub_labels = [_label(st.session_state.sheets[idx]) for idx in indices]
                sub_tabs = st.tabs(sub_labels)
                for sub_tab_obj, gi in zip(sub_tabs, indices):
                    flat_iter.append((sub_tab_obj, gi, indices))

    for sub_tab, i, peer_indices in flat_iter:
        peer_pos = peer_indices.index(i)
        peer_first = (peer_pos == 0)
        peer_last = (peer_pos == len(peer_indices) - 1)
        sheet = st.session_state.sheets[i]
        with sub_tab:
            # Colored type badge + sheet name header
            badge_label, badge_color = TYPE_BADGE.get(sheet.get('type', 'sql'), ('—', '#6b7280'))
            st.markdown(
                f"""
                <div style='display:flex; align-items:center; gap:0.6rem; margin-bottom:0.5rem;'>
                    <span style='background:{badge_color}; color:#ffffff !important;
                                 font-size:0.72rem; font-weight:700; letter-spacing:0.05em;
                                 padding:0.2rem 0.55rem; border-radius:6px;'>{badge_label}</span>
                    <span style='font-size:1.05rem; font-weight:600; color:#1a1a2e;'>{sheet['name']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Scheme tab is read-only — no run/delete buttons
            if sheet.get('type') == 'scheme':
                st.caption("📋 Reference scheme (read-only). To update, edit `scheme.csv` in the project folder.")
                if sheet['df'] is not None:
                    st.dataframe(sheet['df'], use_container_width=True, height=600)
                continue

            # Compact toolbar: ⬅️ ➡️ Run | Delete | CSV | Excel  — all in one row
            st.markdown(
                """
                <style>
                .compact-bar .stButton > button,
                .compact-bar .stDownloadButton > button {
                    padding: 0.28rem 0.5rem !important;
                    font-size: 0.85rem !important;
                    min-height: 0 !important;
                    line-height: 1.2 !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div class='compact-bar'>", unsafe_allow_html=True)
            col_run, col_del, col_csv, col_xlsx = st.columns([1, 1, 1, 1])

            with col_run:
                rq = st.session_state.running_query
                this_running = rq and rq['sheet_idx'] == i

                if sheet.get('type') == 'sql':
                    if this_running:
                        # ── Poll: check if done ───────────────────────────
                        if not is_pid_running(rq['pid']):
                            df, err = read_async_result(rq['result_path'], rq['err_path'])
                            sheet['df'] = df
                            sheet['error'] = err
                            sheet['status'] = 'success' if df is not None else 'failed'
                            save_sheets(st.session_state.sheets)
                            st.session_state.running_query = None
                            if df is not None:
                                auto_refresh_kpis(reason=f"after running '{sheet['name']}'")
                            st.rerun()
                        else:
                            # Still running — show Stop button
                            if st.button("⏹ Stop", key=f"run_{i}",
                                         use_container_width=True, type="primary",
                                         help="Cancel running query"):
                                stop_query_process(rq['pid'])
                                st.session_state.running_query = None
                                sheet['status'] = 'cancelled'
                                sheet['error'] = 'Query cancelled by user'
                                st.rerun()
                            # Auto-refresh every second while running
                            time.sleep(1)
                            st.rerun()
                    else:
                        if st.button("▶ Run", key=f"run_{i}",
                                     use_container_width=True, help="Run query",
                                     disabled=bool(rq)):
                            pid, rp, ep = start_query_async(sheet['query'], i)
                            st.session_state.running_query = {
                                'sheet_idx': i, 'pid': pid,
                                'result_path': rp, 'err_path': ep
                            }
                            sheet['status'] = 'running'
                            st.rerun()

                elif sheet.get('type') == 'kpi':
                    if st.button("⚡ Calc", key=f"run_{i}", use_container_width=True, help="Calculate KPI"):
                        with st.spinner("Calculating..."):
                            df, err = execute_kpi(sheet['query'], st.session_state.sheets)
                            sheet['df'] = df
                            sheet['error'] = err
                            sheet['status'] = 'success' if df is not None else 'failed'
                        save_sheets(st.session_state.sheets)
                        st.rerun()
                else:
                    st.markdown("<div style='text-align:center; color:#9ca3af; font-size:0.8rem; padding-top:0.4rem;'>CSV</div>", unsafe_allow_html=True)

            with col_del:
                if st.button("🗑 Delete", key=f"del_{i}", use_container_width=True, help="Remove sheet"):
                    csv_file = get_user_sheets_dir(get_active_username()) / f"{safe_name(sheet['name'])}.csv"
                    if csv_file.exists():
                        csv_file.unlink()
                    st.session_state.sheets.pop(i)
                    save_sheets(st.session_state.sheets)
                    st.rerun()

            if sheet['status'] == 'success' and sheet['df'] is not None:
                df = sheet['df']

                # Pre-compute filtered df using the persisted search value (if any)
                _search_q = st.session_state.get(f"search_{i}", "").strip()
                if _search_q:
                    _mask = df.astype(str).apply(
                        lambda col: col.str.contains(_search_q, case=False, na=False)
                    ).any(axis=1)
                    download_df = df[_mask]
                    suffix = "_filtered"
                else:
                    download_df = df
                    suffix = ""

                sheet_key = f"{sheet['name']}:{len(download_df)}:{_search_q}"
                with col_csv:
                    st.download_button(
                        "⬇ CSV",
                        data=df_to_csv(sheet_key, download_df),
                        file_name=f"{sheet['name']}{suffix}.csv",
                        mime="text/csv",
                        key=f"csv_{i}",
                        use_container_width=True,
                        help=f"Download {len(download_df):,} row(s) as CSV"
                             + (" — filtered view" if _search_q else ""),
                    )
                with col_xlsx:
                    st.download_button(
                        "⬇ Excel",
                        data=download_excel_bytes(sheet_key, {sheet['name']: download_df}),
                        file_name=f"{sheet['name']}{suffix}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"xlsx_{i}",
                        use_container_width=True,
                        help=f"Download {len(download_df):,} row(s) as Excel"
                             + (" — filtered view" if _search_q else ""),
                    )
            st.markdown("</div>", unsafe_allow_html=True)

            # ── Query | Rename Sheet | Rename Columns — all in one line ────
            exp_query, exp_rename_sheet, exp_rename_cols = st.columns(3)

            with exp_query:
                if sheet.get('type') == 'sql' and sheet.get('query'):
                    with st.expander("🟦 SQL Query", expanded=False):
                        edit_key = f"sql_editmode_{i}"
                        in_edit = st.session_state.get(edit_key, False)

                        if not in_edit:
                            # Read-only highlighted view
                            st.code(sheet['query'], language='sql')
                            if st.button("✏️ Edit Query", key=f"sql_editbtn_{i}",
                                         use_container_width=True):
                                st.session_state[edit_key] = True
                                st.rerun()
                        else:
                            # Edit mode
                            new_q = st.text_area(
                                "Edit & re-run",
                                value=sheet['query'],
                                height=200,
                                key=f"sql_edit_{i}",
                                help="Modify and click Save or Run."
                            )
                            b1, b2, b3 = st.columns(3)
                            with b1:
                                if st.button("💾 Save", key=f"sql_save_{i}",
                                             use_container_width=True,
                                             disabled=(new_q == sheet['query'])):
                                    sheet['query'] = new_q
                                    save_sheets(st.session_state.sheets)
                                    st.session_state[edit_key] = False
                                    st.rerun()
                            with b2:
                                rq = st.session_state.running_query
                                other_running = bool(rq) and rq.get('sheet_idx') != i
                                if st.button("▶ Run Updated", key=f"sql_run_inline_{i}",
                                             use_container_width=True, type="primary",
                                             disabled=other_running):
                                    if new_q != sheet['query']:
                                        sheet['query'] = new_q
                                        save_sheets(st.session_state.sheets)
                                    pid, rp, ep = start_query_async(sheet['query'], i)
                                    st.session_state.running_query = {
                                        'sheet_idx': i, 'pid': pid,
                                        'result_path': rp, 'err_path': ep
                                    }
                                    sheet['status'] = 'running'
                                    st.session_state[edit_key] = False
                                    st.rerun()
                            with b3:
                                if st.button("✗ Cancel", key=f"sql_cancel_{i}",
                                             use_container_width=True):
                                    st.session_state[edit_key] = False
                                    st.rerun()

                elif sheet.get('type') == 'kpi' and sheet.get('query'):
                    with st.expander("🟧 KPI / Formula", expanded=False):
                        edit_key = f"kpi_editmode_{i}"
                        in_edit = st.session_state.get(edit_key, False)

                        if not in_edit:
                            st.code(sheet['query'], language='sql')
                            if st.button("✏️ Edit Formula", key=f"kpi_editbtn_{i}",
                                         use_container_width=True):
                                st.session_state[edit_key] = True
                                st.rerun()
                        else:
                            new_q = st.text_area(
                                "Edit & re-run",
                                value=sheet['query'],
                                height=200,
                                key=f"kpi_edit_{i}"
                            )
                            b1, b2, b3 = st.columns(3)
                            with b1:
                                if st.button("💾 Save", key=f"kpi_save_{i}",
                                             use_container_width=True,
                                             disabled=(new_q == sheet['query'])):
                                    sheet['query'] = new_q
                                    save_sheets(st.session_state.sheets)
                                    st.session_state[edit_key] = False
                                    st.rerun()
                            with b2:
                                if st.button("⚡ Run Updated", key=f"kpi_run_inline_{i}",
                                             use_container_width=True, type="primary"):
                                    if new_q != sheet['query']:
                                        sheet['query'] = new_q
                                    with st.spinner("Calculating..."):
                                        df, err = execute_kpi(sheet['query'], st.session_state.sheets)
                                    sheet['df']     = df
                                    sheet['error']  = err
                                    sheet['status'] = 'success' if df is not None else 'failed'
                                    save_sheets(st.session_state.sheets)
                                    st.session_state[edit_key] = False
                                    st.rerun()
                            with b3:
                                if st.button("✗ Cancel", key=f"kpi_cancel_{i}",
                                             use_container_width=True):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                        available = [s['name'] for s in st.session_state.sheets if s.get('df') is not None and s.get('type') != 'kpi']
                        if available:
                            st.caption("Tables: " + ", ".join(f"`{n}`" for n in available))

            with exp_rename_sheet:
                with st.expander("✏️ Rename Sheet"):
                    new_name = st.text_input(
                        "New name", value=sheet['name'],
                        key=f"sheet_rename_input_{i}"
                    )
                    if st.button("Save Name", key=f"sheet_rename_btn_{i}", type="primary", use_container_width=True):
                        new_name_clean = new_name.strip()
                        if not new_name_clean:
                            st.error("Name cannot be empty")
                        elif new_name_clean == sheet['name']:
                            st.info("No change")
                        elif new_name_clean in [s['name'] for s in st.session_state.sheets]:
                            st.error(f"A sheet named '{new_name_clean}' already exists")
                        else:
                            old_name = sheet['name']
                            user_dir = get_user_sheets_dir(get_active_username())
                            old_csv = user_dir / f"{safe_name(old_name)}.csv"
                            new_csv = user_dir / f"{safe_name(new_name_clean)}.csv"
                            try:
                                if old_csv.exists():
                                    old_csv.rename(new_csv)
                            except Exception:
                                pass
                            sheet['name'] = new_name_clean
                            save_sheets(st.session_state.sheets)
                            st.success(f"Renamed '{old_name}' → '{new_name_clean}'")
                            st.caption("⚠️ If any KPI query referenced the old name, edit and update it.")
                            st.rerun()

            with exp_rename_cols:
                if sheet.get('df') is not None and len(sheet['df'].columns) > 0:
                    with st.expander("Rename Columns"):
                        st.caption("Edit any column name and click **Apply**.")
                        cols = list(sheet['df'].columns)
                        new_names = {}
                        for chunk_start in range(0, len(cols), 2):
                            chunk = cols[chunk_start:chunk_start + 2]
                            cs = st.columns(len(chunk))
                            for col_idx, c in enumerate(chunk):
                                with cs[col_idx]:
                                    new_names[c] = st.text_input(
                                        label=c, value=c,
                                        key=f"rename_{i}_{c}_{chunk_start + col_idx}"
                                    )
                        btn_col_a, btn_col_b = st.columns(2)
                        with btn_col_a:
                            if st.button("Apply", key=f"rename_apply_{i}", type="primary", use_container_width=True):
                                mapping = {old: new for old, new in new_names.items() if new and new != old}
                                if mapping:
                                    projected = [new_names.get(c, c) for c in cols]
                                    if len(set(projected)) != len(projected):
                                        st.error("Duplicate column names — pick unique names.")
                                    elif any(not n.strip() for n in projected):
                                        st.error("Names cannot be empty.")
                                    else:
                                        sheet['df'] = sheet['df'].rename(columns=mapping)
                                        save_sheets(st.session_state.sheets)
                                        st.success(f"Renamed {len(mapping)} column(s)")
                                        st.rerun()
                                else:
                                    st.info("No changes made.")
                        with btn_col_b:
                            if st.button("Reset", key=f"rename_reset_{i}", use_container_width=True):
                                st.rerun()

            # Show data
            if sheet['status'] == 'pending' and sheet.get('type') == 'sql':
                st.info("Click **Run Query** to load data.")
            elif sheet['status'] == 'pending' and sheet.get('type') == 'kpi':
                st.info("Click **Calculate KPI** to evaluate the formula.")
            elif sheet['status'] == 'failed' and sheet.get('type') == 'kpi':
                # Smart-fix UI for KPI errors
                explain, fixed_q = smart_fix_kpi_error(sheet.get('query', ''), sheet.get('error', '') or '', st.session_state.sheets)
                if explain:
                    st.warning(f"**Smart Fix Suggestion:**\n\n{explain}")
                    if fixed_q and fixed_q != sheet.get('query'):
                        st.code(fixed_q, language='sql')
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("Apply Fix & Re-run", key=f"fix_apply_{i}", type="primary", use_container_width=True):
                                sheet['query'] = fixed_q
                                df, err = execute_kpi(fixed_q, st.session_state.sheets)
                                sheet['df'] = df
                                sheet['error'] = err
                                sheet['status'] = 'success' if df is not None else 'failed'
                                save_sheets(st.session_state.sheets)
                                st.rerun()
                        with col_b:
                            if st.button("Apply Fix Only", key=f"fix_save_{i}", use_container_width=True):
                                sheet['query'] = fixed_q
                                save_sheets(st.session_state.sheets)
                                st.rerun()
            elif sheet['status'] == 'failed':
                st.error(f"Query failed: {sheet['error']}")
            elif sheet['df'] is not None:
                df = sheet['df']

                # ── (E) Search filter ─────────────────────────────────────
                search_col, info_col = st.columns([2, 3])
                with search_col:
                    q = st.text_input(
                        "🔍 Search (any column)",
                        key=f"search_{i}",
                        placeholder="Type to filter rows…",
                        label_visibility="collapsed",
                    )
                if q.strip():
                    mask = df.astype(str).apply(
                        lambda col: col.str.contains(q, case=False, na=False)
                    ).any(axis=1)
                    filtered = df[mask]
                else:
                    filtered = df
                total_rows = len(filtered)
                with info_col:
                    if q.strip():
                        st.caption(f"**{total_rows:,}** of {len(df):,} rows × {len(df.columns)} columns (filtered)")
                    else:
                        st.caption(f"**{total_rows:,}** rows × {len(df.columns)} columns")

                PAGE_SIZE = 500
                if total_rows > PAGE_SIZE:
                    page_count = (total_rows - 1) // PAGE_SIZE + 1
                    page = st.number_input(
                        f"Page (1–{page_count})", min_value=1, max_value=page_count,
                        value=1, step=1, key=f"page_{i}"
                    )
                    start = (page - 1) * PAGE_SIZE
                    st.dataframe(filtered.iloc[start: start + PAGE_SIZE], use_container_width=True, height=500)
                else:
                    st.dataframe(filtered, use_container_width=True, height=min(500, 35 * total_rows + 38))


def render_cj_level(sheets):
    """VLOOKUP-style merge of all KPI incentive sheets into one CJ-level table."""
    import io

    st.markdown("### 👤 CJ Level — Consolidated Incentive")

    if not DUCKDB_AVAILABLE:
        st.error("DuckDB not installed. Run: pip install duckdb")
        return

    # All sheets that have data (exclude scheme)
    data_sheets = [s for s in sheets if s.get('df') is not None and s.get('type') != 'scheme']
    if not data_sheets:
        st.info("No data sheets loaded yet. Add KPI sheets from the sidebar first.")
        return

    ID_CANDIDATES = ['inspection_by', 'employee_email', 'cj_email', 'email', 'inspector']

    # ── Step 1: Map each sheet → key col + value col ──────────────────────
    st.markdown("#### Configure VLOOKUP mapping")
    st.caption("For each KPI sheet, select the CJ identifier column and the incentive value column.")

    # Group All/Clear button colour cues — green for All, red for Clear when active
    st.markdown("""
    <style>
        /* ✓ All — green when active (primary) */
        button[data-testid="stBaseButton-primary"]:has(div:contains("✓ All")),
        div[data-testid="stButton"] button[kind="primary"]:has(p:contains("✓ All")) {
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
            box-shadow: 0 4px 14px rgba(22,163,74,0.35) !important;
            border: none !important;
        }
        /* ✗ Clear — red when active (primary) */
        button[data-testid="stBaseButton-primary"]:has(div:contains("✗ Clear")),
        div[data-testid="stButton"] button[kind="primary"]:has(p:contains("✗ Clear")) {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
            box-shadow: 0 4px 14px rgba(220,38,38,0.35) !important;
            border: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Group sheets by type
    GROUP_LABELS = [
        ('sql', '🟦 Queries'),
        ('csv', '🟩 Manual'),
        ('kpi', '🟧 KPIs'),
    ]

    mappings = []
    for gtype, glabel in GROUP_LABELS:
        group_sheets = [s for s in data_sheets if s.get('type') == gtype]
        if not group_sheets:
            continue

        # Group open/close state — default collapsed
        open_key = f"cjl_grp_open_{gtype}"
        if open_key not in st.session_state:
            st.session_state[open_key] = False
        is_open = st.session_state[open_key]

        # Compute current state to highlight the active button
        included_count = sum(
            1 for s in group_sheets
            if st.session_state.get(f"cjl_inc_{s['name']}", True)
        )
        all_on  = included_count == len(group_sheets)
        all_off = included_count == 0
        all_btn_type   = "primary" if all_on  else "secondary"
        clear_btn_type = "primary" if all_off else "secondary"

        chev_col, hdr_col, sel_col, clr_col = st.columns([0.5, 3.5, 1, 1])
        with chev_col:
            chevron = "▼" if is_open else "▶"
            if st.button(chevron, key=f"cjl_grp_toggle_{gtype}", use_container_width=True,
                         help="Show/hide this group"):
                st.session_state[open_key] = not is_open
                st.rerun()
        with hdr_col:
            mix_note = "" if (all_on or all_off) else f" · {included_count}/{len(group_sheets)} on"
            st.markdown(f"**{glabel}** ({len(group_sheets)}){mix_note}")
        with sel_col:
            if st.button("✓ All", key=f"cjl_selall_{gtype}", use_container_width=True,
                         type=all_btn_type,
                         help=f"Include all sheets in {glabel}"):
                for s in group_sheets:
                    st.session_state[f"cjl_inc_{s['name']}"] = True
                st.rerun()
        with clr_col:
            if st.button("✗ Clear", key=f"cjl_clrall_{gtype}", use_container_width=True,
                         type=clear_btn_type,
                         help=f"Exclude all sheets in {glabel}"):
                for s in group_sheets:
                    st.session_state[f"cjl_inc_{s['name']}"] = False
                st.rerun()

        if not is_open:
            # Group collapsed — build mappings silently from session state so the merge still works.
            for s in group_sheets:
                include = st.session_state.get(f"cjl_inc_{s['name']}", True)
                if not include:
                    continue
                key_col = st.session_state.get(f"cjl_key_{s['name']}")
                val_cols_stored = st.session_state.get(f"cjl_vals_{s['name']}", [])
                label_prefix = st.session_state.get(f"cjl_lbl_{s['name']}", s['name'])
                if not key_col or not val_cols_stored:
                    continue  # widgets never rendered yet — skip until user opens the group
                for vc in val_cols_stored:
                    final_label = label_prefix if len(val_cols_stored) == 1 else f"{label_prefix}__{vc}"
                    mappings.append({
                        'sheet_name': s['name'],
                        'df': s['df'],
                        'key_col': key_col,
                        'val_col': vc,
                        'label': final_label
                    })
            st.markdown("")  # gap
            continue

        for s in group_sheets:
            df = s['df']
            cols = list(df.columns)
            cols_lower = {c.lower(): c for c in cols}

            default_key = next((cols_lower[c] for c in ID_CANDIDATES if c in cols_lower), cols[0])
            default_val_cols = [
                c for c in cols
                if any(k in c.lower() for k in ['incentive', 'bonus', 'payout'])
            ]
            if not default_val_cols:
                default_val_cols = [cols[1]] if len(cols) > 1 else []

            with st.expander(f"📄 {s['name']}", expanded=False):
                c1, c2, c3 = st.columns([1, 2, 3])
                with c1:
                    include = st.checkbox("Include", value=True, key=f"cjl_inc_{s['name']}")
                with c2:
                    key_col = st.selectbox(
                        "CJ Key column",
                        options=cols,
                        index=cols.index(default_key),
                        key=f"cjl_key_{s['name']}"
                    )
                with c3:
                    val_cols = st.multiselect(
                        "Incentive columns (pick one or more)",
                        options=cols,
                        default=default_val_cols,
                        key=f"cjl_vals_{s['name']}"
                    )
                if include and val_cols:
                    label_prefix = st.text_input(
                        "Label prefix in final table",
                        value=s['name'],
                        key=f"cjl_lbl_{s['name']}",
                        help="Final column = '{prefix}_{column}'. Use just '{prefix}' if only one column selected."
                    )
                    for vc in val_cols:
                        # If only one value column, use prefix as the final label.
                        # Otherwise, combine prefix + value column name to keep them unique.
                        final_label = label_prefix if len(val_cols) == 1 else f"{label_prefix}__{vc}"
                        mappings.append({
                            'sheet_name': s['name'],
                            'df': df,
                            'key_col': key_col,
                            'val_col': vc,
                            'label': final_label
                        })
                elif include and not val_cols:
                    st.warning(f"Pick at least one incentive column for {s['name']}.")

        st.markdown("")  # small gap between groups

    # ── Action bar — always visible, separated from the group section ────
    st.divider()

    has_mappings = len(mappings) > 0
    if not has_mappings:
        st.info("ℹ️ Open a group above and select sheets to enable the Merge button.")

    btn_col, clear_col = st.columns([2, 1])
    with btn_col:
        clicked = st.button(
            f"🔗 Merge All (VLOOKUP) — {len(mappings)} sheet(s) selected",
            type="primary",
            use_container_width=True,
            key="cjl_merge_btn",
            disabled=not has_mappings,
        )
    with clear_col:
        if st.button("🗑 Clear Result", use_container_width=True, key="cjl_clear_btn"):
            st.session_state.pop('cjl_merged_df', None)
            st.session_state.pop('cjl_label_cols', None)
            st.rerun()

    if not has_mappings:
        return

    # ── Step 2: Build merged table and store in session state ─────────────
    if clicked:
        try:
            con = duckdb.connect()
            label_cols = []

            for idx, m in enumerate(mappings):
                df = m['df'][[m['key_col'], m['val_col']]].copy()
                df.columns = ['cj_id', m['label']]
                df['cj_id'] = df['cj_id'].astype(str).str.strip().str.lower()
                df[m['label']] = pd.to_numeric(df[m['label']], errors='coerce').fillna(0)
                df = df.groupby('cj_id', as_index=False)[m['label']].sum()
                con.register(f'_t{idx}', df)
                label_cols.append(m['label'])

            query = "SELECT * FROM _t0"
            for idx in range(1, len(mappings)):
                query = f"SELECT * FROM ({query}) _base FULL OUTER JOIN _t{idx} USING (cj_id)"

            merged = con.execute(query).df()
            con.close()

            for c in label_cols:
                if c in merged.columns:
                    merged[c] = pd.to_numeric(merged[c], errors='coerce').fillna(0)

            merged['Total Incentive'] = merged[label_cols].sum(axis=1)
            merged = merged.sort_values('Total Incentive', ascending=False).reset_index(drop=True)
            merged = merged.rename(columns={'cj_id': 'CJ (inspection_by)'})

            # Persist result so it survives reruns
            st.session_state['cjl_merged_df'] = merged
            st.session_state['cjl_label_cols'] = label_cols

        except Exception as e:
            st.error(f"Merge failed: {e}")
            return

    # ── Display stored result (survives reruns) ───────────────────────────
    if 'cjl_merged_df' not in st.session_state:
        return

    merged     = st.session_state['cjl_merged_df']
    label_cols = st.session_state['cjl_label_cols']

    # ── Step 3: Summary cards ─────────────────────────────────────────────
    total_cjs    = len(merged)
    total_payout = int(merged['Total Incentive'].sum())
    avg_payout   = int(merged['Total Incentive'].mean())
    top_earner   = merged.iloc[0]['CJ (inspection_by)'] if total_cjs else "—"

    def _card(label, value, color, icon):
        return (
            f"<div style='background:#ffffff;border-left:5px solid {color};"
            f"border-radius:10px;padding:0.9rem 1.1rem;margin-bottom:0.5rem;"
            f"box-shadow:0 2px 6px rgba(0,0,0,0.06);'>"
            f"<div style='font-size:0.72rem;font-weight:600;color:#6b7280;"
            f"text-transform:uppercase;letter-spacing:0.05em;'>{icon} {label}</div>"
            f"<div style='font-size:1.5rem;font-weight:700;color:{color};'>{value}</div>"
            f"</div>"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(_card("Total CJs",    total_cjs,            "#2563eb", "👤"), unsafe_allow_html=True)
    with c2: st.markdown(_card("Total Payout", f"₹{total_payout:,}", "#16a34a", "💰"), unsafe_allow_html=True)
    with c3: st.markdown(_card("Avg / CJ",     f"₹{avg_payout:,}",  "#7c3aed", "📊"), unsafe_allow_html=True)
    with c4: st.markdown(_card("Top Earner",   str(top_earner),      "#d97706", "🏆"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 4: Search + table ────────────────────────────────────────────
    search = st.text_input("🔍 Search CJ", placeholder="Filter by email / name", key="cj_level_search")
    display_df = merged.copy()
    if search:
        display_df = display_df[
            display_df['CJ (inspection_by)'].astype(str).str.contains(search, case=False, na=False)
        ]

    st.dataframe(display_df, use_container_width=True, height=500)
    st.caption(f"{len(display_df)} CJs · ₹{int(display_df['Total Incentive'].sum()):,} total payout")

    # ── Step 5: Download ──────────────────────────────────────────────────
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "⬇ CSV", data=display_df.to_csv(index=False).encode(),
            file_name="cj_level_incentives.csv", mime="text/csv",
            use_container_width=True
        )
    with dl2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            display_df.to_excel(writer, index=False, sheet_name='CJ_Level')
        st.download_button(
            "⬇ Excel", data=buf.getvalue(),
            file_name="cj_level_incentives.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


def main():
    """Main entry point"""
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()


if __name__ == '__main__':
    main()

"""
Standalone Snowflake query runner — called as a subprocess from streamlit_app.py
Reads SQL from stdin, writes JSON results to stdout.
Snowflake user / role / account / warehouse come from environment variables,
which the parent process sets per-user.
"""
import os
import sys
import json
from snowflake.connector import connect


def main():
    query = sys.stdin.read().strip()
    if not query:
        sys.stderr.write("No query provided\n")
        sys.exit(1)

    sf_user      = os.environ.get('SF_USER',      '').strip()
    sf_account   = os.environ.get('SF_ACCOUNT',   'CQ31887-CARS24CSPL').strip()
    sf_role      = os.environ.get('SF_ROLE',      '').strip()
    sf_warehouse = os.environ.get('SF_WAREHOUSE', '').strip()

    if not sf_user:
        sys.stderr.write("SF_USER environment variable is not set. Configure your Snowflake email in the app.\n")
        sys.exit(1)

    # Redirect stdout -> stderr during auth so SSO messages don't pollute JSON output
    real_stdout = sys.stdout
    sys.stdout = sys.stderr

    try:
        conn_kwargs = dict(
            user=sf_user,
            account=sf_account,
            authenticator='externalbrowser',
        )
        if sf_role:
            conn_kwargs['role'] = sf_role
        if sf_warehouse:
            conn_kwargs['warehouse'] = sf_warehouse

        conn = connect(**conn_kwargs)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        result = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        sys.stdout = real_stdout
        sys.stdout.write(json.dumps({"__error__": str(e)}) + "\n")
        sys.exit(1)

    # Restore stdout and write only JSON
    sys.stdout = real_stdout
    sys.stdout.write(json.dumps(result, default=str) + "\n")


if __name__ == '__main__':
    main()

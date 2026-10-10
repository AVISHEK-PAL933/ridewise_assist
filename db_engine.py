import sqlite3
import pandas as pd
import re
import os

DB_PATH = "ridewise.db"

SCHEMA_CONTEXT = """
SQLite Schema (ridewise.db):
1. customers (customer_id TEXT PK, full_name TEXT, phone TEXT, email TEXT, city TEXT, date_of_birth TEXT, driving_license_no TEXT, kyc_status TEXT, customer_tier TEXT, created_at TEXT)
2. vehicles (vehicle_id TEXT PK, registration_no TEXT, vehicle_type TEXT, model TEXT, hub_name TEXT, hourly_rate REAL, daily_rate REAL, battery_capacity_kwh REAL, status TEXT, commissioned_on TEXT)
3. bookings (booking_id TEXT PK, customer_id TEXT FK, vehicle_id TEXT FK, booked_at TEXT, scheduled_start TEXT, scheduled_end TEXT, actual_return_at TEXT, cancelled_at TEXT, booking_status TEXT, return_battery_pct INTEGER)
   - booking_status values: UPC (Upcoming), ONG (Ongoing), CMP (Completed), CNL_U (Cancelled by customer), CNL_S (Cancelled by RideWise), NSH (No-show)
4. payments (payment_id TEXT PK, booking_id TEXT FK, payment_type TEXT, amount REAL, gst_amount REAL, payment_method TEXT, payment_status TEXT, transaction_ref TEXT, paid_at TEXT, remarks TEXT)
   - payment_type values: BOOKING, DEPOSIT, PENALTY, REFUND
   - amount is in INR excluding 18% GST. Total amount paid = amount + gst_amount. Refunds have negative amounts.
   - Note: payments connects to customer through bookings.booking_id. To query payments for a customer, JOIN bookings ON payments.booking_id = bookings.booking_id WHERE bookings.customer_id = '...'.
5. damage_reports (report_id TEXT PK, booking_id TEXT FK, vehicle_id TEXT FK, reported_by TEXT, damage_category TEXT, severity TEXT, description TEXT, assessed_cost REAL, claim_status TEXT, reported_at TEXT)
   - claim_status values: OPEN, CHARGED, WAIVED, DISPUTED
   - Note: damage_reports connects to customer through bookings.booking_id. To query damage reports for a customer, JOIN bookings ON damage_reports.booking_id = bookings.booking_id WHERE bookings.customer_id = '...'.
"""

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        "ridewise.db",
        "ridewise-assist/ridewise.db",
        "../ridewise.db",
        os.path.join(base_dir, "ridewise.db"),
        os.path.join(base_dir, "ridewise-assist", "ridewise.db"),
        os.path.join(base_dir, "..", "ridewise.db")
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.getsize(p) > 10000:
            return p
    return DB_PATH

def execute_sql(sql_query: str):
    """Executes read-only SQL on ridewise.db."""
    clean_sql = sql_query.strip()
    clean_sql_upper = clean_sql.upper()

    # Block multi-statement queries (semicolon followed by SQL statement)
    statements = [s.strip() for s in clean_sql.split(";") if s.strip()]
    if len(statements) > 1:
        return None, "Forbidden: Multi-statement SQL queries are strictly prohibited."

    single_sql = statements[0] if statements else clean_sql_upper
    single_sql_upper = single_sql.upper()

    # Ensure query starts with SELECT or WITH
    if not (single_sql_upper.startswith("SELECT") or single_sql_upper.startswith("WITH")):
        return None, "Forbidden: Only read-only SELECT or WITH statements are allowed."

    # Block forbidden mutation keywords
    forbidden_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", 
        "TRUNCATE", "REPLACE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "GRANT", "REVOKE"
    ]
    for word in forbidden_keywords:
        if re.search(r'\b' + word + r'\b', single_sql_upper):
            return None, f"Forbidden: '{word}' statements are strictly prohibited. Only read-only SELECT queries are allowed."

    try:
        db_file = get_db_path()
        conn = sqlite3.connect(db_file)
        df = pd.read_sql_query(single_sql, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

def run_self_healing_sql(client, model_name: str, query: str, role: str, customer_id: str = None, retries: int = 2):
    """Generates SQL, executes it against SQLite, and automatically recovers from syntax errors."""
    if role == "customer":
        role_constraint = f"""
STRICT SECURITY SCOPING:
- The current user is a CUSTOMER with ID '{customer_id}'.
- You MUST restrict all queries touching customers, bookings, payments, or damage_reports to ONLY customer_id = '{customer_id}'.
- For payments or damage_reports, JOIN bookings ON payments.booking_id = bookings.booking_id WHERE bookings.customer_id = '{customer_id}'.
- NEVER query global fleet metrics, company revenue, or records belonging to other customers.
"""
    else:
        role_constraint = """
ROLE SCOPING:
- The current user is a SUPPORT AGENT with full read access to all customers, bookings, payments, vehicles, and damage reports.
"""

    system_prompt = f"""You are an expert SQLite translator for the RideWise mobility system.
{SCHEMA_CONTEXT}
{role_constraint}

RULES:
1. Return ONLY valid SQLite SELECT SQL wrapped in ```sql ... ``` block.
2. Do not include markdown commentary or extra text outside the code block.
3. Ensure date filters and calculations are standard SQLite functions.
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    last_sql = ""
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.0
            )
            content = response.choices[0].message.content or ""
        except Exception as e:
            return None, "", f"LLM API Error: {str(e)}"

        match = re.search(r"```(?:sql)?\s*(.*?)\s*```", content, re.DOTALL)
        sql = match.group(1).strip() if match else content.strip()
        last_sql = sql

        # Deterministic Guardrail Check for Customer Role
        if role == "customer" and customer_id:
            sql_lower = sql.lower()
            # 1. Check if querying another customer's explicit ID
            other_cust_ids = re.findall(r'cust\d{4}', sql_lower)
            for cid in other_cust_ids:
                if cid != customer_id.lower():
                    return None, sql, f"Guardrail Alert: Access denied. Customer queries cannot inspect records belonging to other customer IDs ({cid.upper()})."

            # 2. Check if customer_id missing from queries touching customer tables
            touches_customer_tables = any(tbl in sql_lower for tbl in ["customers", "bookings", "payments", "damage_reports"])
            if touches_customer_tables and customer_id.lower() not in sql_lower:
                return None, sql, f"Guardrail Alert: Customer queries must be scoped to your customer ID ({customer_id}). Access to global fleet data or other customer records is restricted."

        df, err = execute_sql(sql)
        if err is None:
            return df, sql, None

        # Self-healing feedback loop: pass error back to model
        messages.append({"role": "assistant", "content": content})
        messages.append({
            "role": "user",
            "content": f"The executed SQL failed with SQLite error: '{err}'. Please revise and return only the corrected SQL."
        })

    return None, last_sql, f"SQL Execution failed after {retries + 1} attempts. Last error: {err}"
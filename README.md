# 🛵 RideWise Assist — Enterprise Conversational AI & Analytics Platform

RideWise Assist is a state-of-the-art multi-engine conversational AI assistant designed for a two-wheeler and EV rental enterprise. It integrates structured SQLite database queries, unstructured PDF rental policy vector retrieval (FAISS), and natural-language Excel workbook analytics (`ridewise_data.xlsx`) into a sleek, unified Streamlit dashboard powered by Azure OpenAI (`Neo-Hackathon`).

---

## 🏛️ Project Architecture

```
Ride_Wise_Assist/
├── app.py                      # Main Streamlit UI & Multi-Engine Router
├── db_engine.py                # SQL Engine with Read-Only Validation & Scoping Guardrails
├── policy_engine.py            # FAISS Vector Search over Policy PDFs (SentenceTransformers)
├── excel_engine.py             # Deterministic Pandas Analytics over ridewise_data.xlsx
├── ridewise.db                 # SQLite Database (Customers, Vehicles, Bookings, Payments, Damages)
├── ridewise_data.xlsx          # 5-Sheet Workbook (200 Customers, 60 Vehicles, 1800 Bookings...)
├── documents/                  # 5 Core Rental & Policy PDFs
│   ├── 01_Rental_Agreement_and_Terms.pdf
│   ├── 02_Cancellation_and_Refund_Policy_v1.pdf
│   ├── 03_Cancellation_and_Refund_Policy_v2.pdf
│   ├── 04_Late_Return_and_Damage_Penalty_Schedule.pdf
│   └── 05_EV_User_Guide_and_FAQ.pdf
├── tests/                      # Modular Automated Test Suite
│   ├── test_database.py
│   ├── test_db_engine.py
│   ├── test_policy_engine.py
│   ├── test_excel_engine.py
│   └── test_security.py
├── .streamlit/
│   └── config.toml             # Dark Obsidian & Emerald UI Theme Configuration
├── .env.example                # Template for Environment Configuration
├── requirements.txt            # Python Dependencies
└── README.md                   # System Documentation
```

---

## 🔒 Security & Data Isolation Architecture

1. **Strict Read-Only SQL Engine**:
   - Parses and validates generated SQL prior to execution.
   - Rejects non-`SELECT` keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `ATTACH`, `PRAGMA`).
   - Disallows multi-statement semicolon injections.

2. **Customer Tenant Isolation**:
   - For `Customer` role sessions, all queries are automatically forced to contain `WHERE customer_id = 'CUSTXXXX'`.
   - Cross-tenant requests (e.g. `CUST0001` attempting to query `CUST0005`) are immediately blocked by pre-execution guardrails before hitting the database.

3. **Deterministic Excel Operations**:
   - Excel analytics run via deterministic `pandas` filtering and aggregations rather than executing arbitrary LLM code snippets.

4. **Credential Safety**:
   - Azure OpenAI credentials remain strictly inside `.env` (never committed or printed in logs).

---

## ⚡ Quick Start Guide

### 1. Prerequisites & Virtual Environment Setup
Ensure Python 3.9+ is installed. Open PowerShell in the project root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in your Azure OpenAI credentials:
```env
AZURE_OPENAI_ENDPOINT=https://<your-endpoint>.openai.azure.com/
AZURE_OPENAI_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT_NAME=Neo-Hackathon
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 3. Launching the Streamlit Application
```powershell
streamlit run app.py
```
Access the application at `http://localhost:8501` (or port specified in terminal output).

---

## 🧪 Running Automated Tests

Run the complete modular test suite using `unittest` or `pytest`:

```powershell
# Run individual test modules:
python -m unittest discover -s tests -p "test_*.py"

# Or run pytest:
pytest tests/
```

---

## 📊 Domain Data Model Summary

| Table / Sheet Name | Row Count | Key Attributes |
| :--- | :--- | :--- |
| `customers` | **200** | `customer_id`, `full_name`, `kyc_status`, `membership_tier` |
| `vehicles` | **60** | `vehicle_id`, `model`, `category` (EV/Fuel), `daily_rate_inr` |
| `bookings` | **1800** | `booking_id`, `customer_id`, `vehicle_id`, `start_date`, `booking_status` |
| `payments` | **3289** | `payment_id`, `booking_id`, `amount`, `gst_amount`, `payment_type` |
| `damage_reports` | **80** | `report_id`, `booking_id`, `damage_type`, `estimated_repair_cost` |

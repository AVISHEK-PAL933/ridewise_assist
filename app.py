import streamlit as st
import pandas as pd
import os
import openai
from db_engine import run_self_healing_sql
from policy_engine import PolicyRetriever

# 1. Page Configuration
st.set_page_config(page_title="RideWise Assist | Enterprise AI", page_icon="🛵", layout="wide")

# 2. Azure OpenAI Client Configuration
AZURE_OPENAI_URL = os.getenv("AZURE_OPENAI_ENDPOINT", "https://neo-hackathon.services.ai.azure.com/openai/v1/")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL", "Neo-Hackathon")

@st.cache_resource
def get_openai_client():
    return openai.OpenAI(base_url=AZURE_OPENAI_URL, api_key=AZURE_OPENAI_KEY)

@st.cache_resource
def get_policy_retriever():
    retriever = PolicyRetriever("documents")
    retriever.load_and_index()
    return retriever

client = get_openai_client()
policy_retriever = get_policy_retriever()

# 3. Premium Professional CSS (Black, Emerald Green & Crisp White Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Dark Obsidian Background */
    .stApp {
        background: radial-gradient(circle at 85% 15%, rgba(34, 197, 94, 0.08) 0%, transparent 45%),
                    radial-gradient(circle at 15% 85%, rgba(34, 197, 94, 0.05) 0%, transparent 45%),
                    #090D14;
        color: #F9FAFB;
    }

    header[data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 1 !important;
    }

    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 5rem !important;
    }

    /* Floating White Frosted Navbar */
    .navbar-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(12px);
        border-radius: 50px;
        padding: 10px 28px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin-bottom: 2rem;
    }
    .navbar-logo, .navbar-logo:hover, .navbar-logo:visited, .navbar-logo:focus {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 800;
        font-size: 1.3rem;
        color: #111827 !important;
        text-decoration: none !important;
    }
    .navbar-logo-icon {
        width: 32px;
        height: 32px;
        background: #22C55E;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        font-size: 0.95rem;
        font-weight: 900;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.4);
    }
    .navbar-logo span {
        color: #22C55E !important;
        text-decoration: none !important;
    }
    .navbar-links {
        display: flex;
        align-items: center;
        gap: 22px;
        list-style: none;
        margin: 0;
        padding: 0;
    }
    .navbar-links a, .navbar-links a:hover, .navbar-links a:visited, .navbar-links a:focus {
        color: #374151 !important;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.9rem;
        transition: color 0.2s ease;
    }
    .navbar-links a:hover {
        color: #22C55E !important;
    }
    .navbar-btn, .navbar-btn:hover, .navbar-btn:visited, .navbar-btn:focus {
        background-color: #22C55E !important;
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 0.88rem;
        padding: 8px 22px;
        border-radius: 30px;
        text-decoration: none !important;
        box-shadow: 0 4px 14px rgba(34, 197, 94, 0.35);
        transition: all 0.2s ease;
    }
    .navbar-btn:hover {
        background-color: #16A34A !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(34, 197, 94, 0.5);
    }

    /* Hero Banner Section */
    .hero-container {
        padding: 1rem 0.5rem 1.8rem 0.5rem;
        text-align: left;
    }
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1.05;
        letter-spacing: -1.5px;
        margin-bottom: 0.8rem;
    }
    .hero-white {
        color: #FFFFFF;
    }
    .hero-green {
        color: #22C55E;
        display: block;
    }
    .hero-subtitle {
        color: #9CA3AF;
        font-size: 1.1rem;
        max-width: 680px;
        line-height: 1.6;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }

    /* KPI Metrics Banner */
    .kpi-row {
        display: flex;
        gap: 16px;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 12px 18px;
        flex: 1;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .kpi-icon {
        font-size: 1.5rem;
        background: rgba(34, 197, 94, 0.12);
        padding: 8px;
        border-radius: 8px;
        color: #22C55E;
    }
    .kpi-val {
        font-size: 1.1rem;
        font-weight: 800;
        color: #FFFFFF;
    }
    .kpi-lbl {
        font-size: 0.78rem;
        color: #9CA3AF;
        font-weight: 500;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937;
    }
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #FFFFFF;
        font-weight: 700;
    }

    /* User Profile Card in Sidebar */
    .user-profile-card {
        background: #1F2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .profile-avatar {
        width: 40px;
        height: 40px;
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid #22C55E;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }

    /* Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.95rem;
        padding: 0.65rem 1.2rem;
        transition: all 0.2s ease-in-out;
        width: 100%;
        box-shadow: 0 4px 14px rgba(34, 197, 94, 0.3);
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #4ADE80 0%, #22C55E 100%);
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.5);
        transform: translateY(-1px);
        color: #FFFFFF;
    }

    /* Input & Select Box styling */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #111827 !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: #22C55E !important;
        box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.25) !important;
    }

    /* Chat Messages Styling */
    [data-testid="stChatMessage"] {
        background-color: #1F2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
    }
    [data-testid="stChatMessage"]:nth-child(even) {
        border-left: 3px solid #22C55E;
        background-color: #111827;
    }

    /* Chat Input */
    div[data-testid="stChatInput"] {
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 12px;
    }
    div[data-testid="stChatInput"]:focus-within {
        border-color: #22C55E;
    }

    /* Floating Chat Avatar Widget at Bottom Right */
    .floating-chat-widget {
        position: fixed;
        bottom: 24px;
        right: 24px;
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 999999;
    }
    .chat-bubble-tooltip {
        background: #FFFFFF;
        color: #111827;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 8px 16px;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        display: flex;
        align-items: center;
        gap: 8px;
        position: relative;
    }
    .chat-bubble-tooltip::after {
        content: '';
        position: absolute;
        right: -6px;
        top: 50%;
        transform: translateY(-50%);
        border-width: 6px 0 6px 6px;
        border-style: solid;
        border-color: transparent transparent transparent #FFFFFF;
    }
    .avatar-circle {
        width: 48px;
        height: 48px;
        background: #111827;
        border: 2px solid #22C55E;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 0 16px rgba(34, 197, 94, 0.5);
    }

    .xai-badge {
        background-color: rgba(34, 197, 94, 0.15);
        color: #22C55E;
        border: 1px solid #22C55E;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# 4. Floating Navbar Header
st.markdown("""
<div class="navbar-container">
    <a href="#" class="navbar-logo">
        <div class="navbar-logo-icon">RW</div>
        RideWise <span>Assist</span>
    </a>
    <ul class="navbar-links">
        <li><a href="#">Home</a></li>
        <li><a href="#">Services</a></li>
        <li><a href="#">Mobility</a></li>
        <li><a href="#">Policy Engine</a></li>
        <li><a href="#">Resources</a></li>
        <li><a href="#">About Us</a></li>
    </ul>
    <a href="#" class="navbar-btn">Contact Us</a>
</div>
""", unsafe_allow_html=True)

# 5. Hero Banner & Executive KPI Metrics Row
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">
        <span class="hero-white">Ride with</span>
        <span class="hero-green">Intelligence</span>
    </h1>
    <p class="hero-subtitle">
        Enterprise AI assistant for RideWise Bengaluru powered by FAISS Vector Retrieval and Explainable AI (XAI) Auditability.
    </p>
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-icon">🛵</div>
            <div>
                <div class="kpi-val">60 Vehicles</div>
                <div class="kpi-lbl">EV & Petrol Fleet</div>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <div>
                <div class="kpi-val">200 Customers</div>
                <div class="kpi-lbl">Bengaluru Hubs</div>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📋</div>
            <div>
                <div class="kpi-val">1,800 Bookings</div>
                <div class="kpi-lbl">Active & Past Rides</div>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">⚡</div>
            <div>
                <div class="kpi-val">FAISS AI Search</div>
                <div class="kpi-lbl">Semantic Policy Retrieval</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. Floating Bottom Right Chat Avatar Widget
st.markdown("""
<div class="floating-chat-widget">
    <div class="chat-bubble-tooltip">
        Need help? Chat with us! <span style="cursor: pointer; color: #9CA3AF; font-size: 0.75rem;">✕</span>
    </div>
    <div class="avatar-circle">
        🛵
    </div>
</div>
""", unsafe_allow_html=True)

# 7. Sidebar Controls
st.sidebar.header("Session Controls")
role = st.sidebar.selectbox("Role", ["customer", "support_agent"], index=0)

if role == "customer":
    customer_id = st.sidebar.text_input("Customer ID", value="CUST0001")
    st.sidebar.markdown(f"""
    <div class="user-profile-card">
        <div class="profile-avatar">👤</div>
        <div>
            <div style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem;">{customer_id}</div>
            <div style="font-size: 0.78rem; color: #22C55E; font-weight: 600;">Customer Account</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    customer_id = None
    st.sidebar.markdown("""
    <div class="user-profile-card">
        <div class="profile-avatar">🛠️</div>
        <div>
            <div style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem;">Support Agent</div>
            <div style="font-size: 0.78rem; color: #F59E0B; font-weight: 600;">Full Fleet Access</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if st.sidebar.button("Start New Conversation"):
    st.session_state.messages = []
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# 8. Dual-Engine AI Assistant & Explainable AI (XAI) Processing
def process_user_query(prompt: str, role: str, customer_id: str):
    prompt_lower = prompt.lower()
    if role == "customer":
        restricted_terms = ["total revenue", "all customers", "fleet revenue", "company profit", "other customers", "cust0002", "cust0003", "how many total vehicles"]
        if any(term in prompt_lower for term in restricted_terms):
            guardrail_msg = "Guardrail Alert: As a customer, you can only query your own bookings, payments, and account data. Access to fleet-wide statistics or other customer records is restricted."
            xai_meta = {
                "intent": "Blocked Security Guardrail",
                "faiss_confidence": "N/A",
                "guardrail_status": "BLOCKED: Customer Scope Violation",
                "tenant_scope": f"CUSTOMER ({customer_id})",
                "rules": ["Customer restricted from fleet revenue/multi-tenant statistics."]
            }
            return guardrail_msg, None, None, None, xai_meta

    # Retrieve relevant Policy documents via FAISS Vector Search
    policy_results = policy_retriever.search(prompt, top_k=2)
    policy_context = ""
    citations = []
    top_confidence = "N/A"
    if policy_results:
        conf_val = policy_results[0].get("confidence_pct", "85.0")
        top_confidence = f"{conf_val}%" if not str(conf_val).endswith('%') else str(conf_val)
        for item in policy_results:
            c_pct = item.get("confidence_pct", "85.0")
            policy_context += f"\n--- Document Citation: {item['source']} (FAISS Match Confidence: {c_pct}%) ---\n{item['text']}\n"
            citations.append({
                "source": item["source"],
                "excerpt": item["text"],
                "confidence_pct": c_pct
            })

    # Retrieve relevant SQLite Data via Self-Healing Engine
    df, sql, sql_err = run_self_healing_sql(
        client=client,
        model_name=MODEL_NAME,
        query=prompt,
        role=role,
        customer_id=customer_id,
        retries=2
    )

    if sql_err and "Guardrail Alert" in sql_err:
        xai_meta = {
            "intent": "Blocked Security Guardrail",
            "faiss_confidence": top_confidence,
            "guardrail_status": "BLOCKED: Unscoped Query",
            "tenant_scope": f"CUSTOMER ({customer_id})",
            "rules": [sql_err]
        }
        return sql_err, sql, None, citations, xai_meta

    data_context = ""
    sql_trace = sql if sql else "No SQL query executed."
    if df is not None and not df.empty:
        data_context = f"\nSQLite Database Query Results:\n{df.to_string(index=False)}\n"
    elif df is not None and df.empty:
        data_context = "\nSQLite Database Query Results: No matching records found.\n"
    elif sql_err:
        data_context = f"\nDatabase Error: {sql_err}\n"

    # Determine XAI Intent Classification
    if df is not None and not df.empty and citations:
        intent_type = "Hybrid RAG (SQLite + FAISS Vector Retrieval)"
    elif df is not None and not df.empty:
        intent_type = "Structured SQLite Database Lookup"
    elif citations:
        intent_type = "FAISS Vector Policy Retrieval"
    else:
        intent_type = "General Conversational Query"

    xai_meta = {
        "intent": intent_type,
        "faiss_confidence": top_confidence,
        "guardrail_status": "PASS: Read-Only Query Enforced",
        "tenant_scope": f"CUSTOMER ({customer_id})" if role == "customer" else "SUPPORT AGENT (Full Fleet)",
        "rules": [
            "18% GST calculation applied (Total = amount + gst_amount)",
            "Refund amounts treated as negative entries",
            "Cancellation policy version checked based on booked_at timestamp"
        ]
    }

    # Synthesize Final Grounded Response
    system_prompt = """You are RideWise Assist, an intelligent AI support assistant for two-wheeler rentals in Bengaluru.
Answer user questions accurately using the provided Database Query Results and Policy Document Excerpts.

RULES FOR ACCURACY & GROUNDING:
1. Payments: 'amount' excludes 18% GST. Total paid = amount + gst_amount. Refunds have negative amounts.
2. Cancellation Policies:
   - Bookings created BEFORE 1 July 2026 follow Cancellation Policy v1 (>=24h: 100%, 6-24h: 50%, <6h: 0%).
   - Bookings created ON/AFTER 1 July 2026 follow Cancellation Policy v2 (>=48h: 100%, 12-48h: 75%, 2-12h: 25%, <2h: 0%).
3. Always explain clearly, professionally, and concisely.
"""
    user_content = f"User Request: {prompt}\n\nUser Role: {role}\nCustomer ID: {customer_id}\n\n{data_context}\n{policy_context}"

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"I retrieved the relevant data, but encountered an error synthesizing the final answer: {str(e)}"

    return answer, sql_trace, df, citations, xai_meta

# Helper function to render XAI Expanders
def render_xai_expanders(sql_trace, df_data, citations, xai_meta):
    # Expander 1: Explainable AI (XAI) & Retrieval Metrics
    with st.expander("🧬 Explainable AI (XAI) & Retrieval Metrics"):
        if xai_meta:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Intent Classification", xai_meta.get("intent", "N/A"))
            with col2:
                st.metric("FAISS Top Match Confidence", xai_meta.get("faiss_confidence", "N/A"))
            with col3:
                st.metric("Security Guardrail", "PASS ✅" if "PASS" in xai_meta.get("guardrail_status", "") else "BLOCKED ❌")

            st.markdown(f"**Tenant Isolation Scope:** `{xai_meta.get('tenant_scope', 'N/A')}`")
            st.markdown("**Applied Grounding Rules:**")
            for rule in xai_meta.get("rules", []):
                st.markdown(f"- {rule}")
        else:
            st.write("No XAI telemetry available for this message.")

    # Expander 2: Auditable SQL Trace
    with st.expander("🔍 Auditable SQL Trace"):
        if sql_trace and sql_trace != "No SQL query executed.":
            st.code(sql_trace, language="sql")
            if df_data is not None:
                st.dataframe(df_data, use_container_width=True)
        else:
            st.write("No database query was required for this response.")

    # Expander 3: FAISS Policy Citations
    with st.expander("📄 FAISS Vector Citations"):
        if citations:
            for cite in citations:
                st.markdown(f"**Source:** `{cite['source']}` &nbsp; <span class='xai-badge'>FAISS Match: {cite.get('confidence_pct', 'N/A')}%</span>", unsafe_allow_html=True)
                st.caption(f"> {cite['excerpt']}")
        else:
            st.write("No policy document citations were required for this response.")

# 9. Main Chat Rendering
if not st.session_state.messages:
    st.markdown("""
    <div style="background-color: rgba(17, 24, 39, 0.8); border: 1px dashed #374151; border-radius: 12px; padding: 2rem; text-align: center; margin-bottom: 1.5rem;">
        <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">⚡</div>
        <h3 style="color: #FFFFFF; margin-bottom: 0.5rem; font-weight: 700;">RideWise Support Assistant Active</h3>
        <p style="color: #9CA3AF; margin-bottom: 1.2rem; font-size: 0.95rem;">Ask any questions regarding your ride bookings, payments, cancellation policies, or damage reports.</p>
    </div>
    """, unsafe_allow_html=True)

# Render Chat History with Collapsible XAI Expanders
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_xai_expanders(
                msg.get("sql_trace"),
                msg.get("df_data"),
                msg.get("citations"),
                msg.get("xai_meta")
            )

# Handle Chat Input
if prompt := st.chat_input("Ask a question about bookings, refunds, or rental policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing request via FAISS & Azure OpenAI..."):
            answer, sql_trace, df_data, citations, xai_meta = process_user_query(prompt, role, customer_id)
            st.markdown(answer)
            render_xai_expanders(sql_trace, df_data, citations, xai_meta)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sql_trace": sql_trace,
        "df_data": df_data,
        "citations": citations,
        "xai_meta": xai_meta
    })

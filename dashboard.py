import streamlit as st
import pandas as pd

from agent import analyze_transaction, execute_recovery
from tools import get_transaction, get_customer_history
from db import transactions_collection, recovery_actions_collection


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="PayPilot AI",
    page_icon="💳",
    layout="wide"
)


# =========================================================
# HEADER
# =========================================================

st.title("💳 PayPilot")
st.caption("AI Payment Operations & Revenue Recovery Agent")

st.divider()


# =========================================================
# LOAD DATA
# =========================================================

transactions = list(
    transactions_collection.find(
        {},
        {"_id": 0}
    )
)

recovery_logs = list(
    recovery_actions_collection.find(
        {},
        {"_id": 0}
    )
)


# =========================================================
# CALCULATE METRICS
# =========================================================

total_transactions = len(transactions)

successful_transactions = sum(
    1 for t in transactions
    if t.get("status") == "SUCCESS"
)

failed_transactions = sum(
    1 for t in transactions
    if t.get("status") == "FAILED"
)

revenue_at_risk = sum(
    t.get("amount", 0)
    for t in transactions
    if t.get("status") == "FAILED"
)

recovered_revenue = sum(
    t.get("amount", 0)
    for t in transactions
    if t.get("status") == "SUCCESS"
)


# =========================================================
# MERCHANT OVERVIEW
# =========================================================

st.subheader("📊 Merchant Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Transactions",
        total_transactions
    )

with col2:
    st.metric(
        "Failed Payments",
        failed_transactions
    )

with col3:
    st.metric(
        "Revenue at Risk",
        f"₹{revenue_at_risk:,.0f}"
    )

with col4:
    st.metric(
        "Recovered Revenue",
        f"₹{recovered_revenue:,.0f}"
    )


st.divider()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("💳 PayPilot")

st.sidebar.caption(
    "AI-powered payment recovery"
)


# Only show currently failed transactions

failed_transactions_list = [
    t for t in transactions
    if t.get("status") == "FAILED"
]


if not failed_transactions_list:

    st.success(
        "🎉 No failed payments currently require recovery."
    )

    st.stop()


transaction_options = [
    t["transaction_id"]
    for t in failed_transactions_list
]


selected_transaction = st.sidebar.selectbox(
    "Select Failed Payment",
    transaction_options
)


# =========================================================
# SESSION STATE
# =========================================================

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "recovery_result" not in st.session_state:
    st.session_state.recovery_result = None


# =========================================================
# SELECT TRANSACTION
# =========================================================

transaction = get_transaction(
    selected_transaction
)

customer = get_customer_history(
    transaction["customer_id"]
)


# =========================================================
# TRANSACTION DETAILS
# =========================================================

st.subheader("🔴 Failed Payment")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**Transaction**")
    st.write(transaction["transaction_id"])

with col2:
    st.markdown("**Customer**")
    st.write(transaction["customer_id"])

with col3:
    st.markdown("**Amount**")
    st.write(f"₹{transaction['amount']:,.2f}")

with col4:
    st.markdown("**Payment Method**")
    st.write(transaction["payment_method"])


st.error(
    f"Failure Reason: {transaction['failure_reason']}"
)


# =========================================================
# CUSTOMER CONTEXT
# =========================================================

st.subheader("👤 Customer Context")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Customer",
        customer.get("name", "Unknown")
    )

with col2:
    st.metric(
        "Transactions",
        customer.get("total_transactions", 0)
    )

with col3:
    st.metric(
        "Successful",
        customer.get("successful_transactions", 0)
    )

with col4:
    st.metric(
        "Customer Type",
        customer.get("customer_type", "Unknown")
    )


# =========================================================
# ANALYZE BUTTON
# =========================================================

st.divider()

if st.button(
    "🧠 Analyze Payment",
    use_container_width=True
):

    with st.spinner(
        "PayPilot is analyzing the payment..."
    ):

        result = analyze_transaction(
            selected_transaction
        )

    st.session_state.analysis_result = result
    st.session_state.recovery_result = None


# =========================================================
# AI ANALYSIS
# =========================================================

result = st.session_state.analysis_result


if result:

    st.divider()

    st.subheader("🧠 PayPilot AI Decision")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### Risk Level")

        risk = result.get(
            "risk_level",
            "UNKNOWN"
        )

        if risk == "LOW":
            st.success("🟢 LOW")

        elif risk == "MEDIUM":
            st.warning("🟡 MEDIUM")

        elif risk == "HIGH":
            st.error("🔴 HIGH")

        else:
            st.info(risk)


    with col2:

        st.markdown("### Recommended Action")

        st.info(
            result.get(
                "recommended_action",
                "UNKNOWN"
            )
        )


    st.markdown("### Analysis")

    st.write(
        result.get(
            "analysis",
            "No analysis available."
        )
    )


    st.markdown("### Reason")

    st.write(
        result.get(
            "reason",
            "No reason provided."
        )
    )


    # =====================================================
    # EXECUTE RECOVERY
    # =====================================================

    st.divider()

    action = result.get(
        "recommended_action"
    )


    if st.session_state.recovery_result is None:

        st.subheader("⚡ Agent Execution")

        st.write(
            "PayPilot has selected the safest recovery action."
        )

        if st.button(
            "▶️ Execute Recovery",
            use_container_width=True
        ):

            with st.spinner(
                "PayPilot is executing recovery..."
            ):

                recovery = execute_recovery(
                    selected_transaction,
                    action,
                    result.get("reason", "")
                )

            st.session_state.recovery_result = recovery

            st.rerun()


# =========================================================
# RECOVERY RESULT
# =========================================================

recovery = st.session_state.recovery_result


if recovery:

    st.divider()

    st.subheader("⚡ Recovery Result")

    action_result = recovery.get(
        "action_result",
        {}
    )

    status = action_result.get(
        "status",
        "UNKNOWN"
    )


    # -----------------------------
    # SUCCESS
    # -----------------------------

    if status == "SUCCESS":

        st.success(
            "✅ PAYMENT RECOVERED SUCCESSFULLY"
        )

        st.metric(
            "Recovered Amount",
            f"₹{transaction['amount']:,.2f}"
        )


    # -----------------------------
    # FALLBACK
    # -----------------------------

    elif status == "FALLBACK_RECOVERY":

        st.warning(
            "🔄 Primary recovery failed — fallback recovery started."
        )

        payment_link = action_result.get(
            "payment_link"
        )

        if payment_link:

            st.info(
                f"Payment Link: {payment_link}"
            )

        st.write(
            "Customer was sent an alternative payment option."
        )


    # -----------------------------
    # PAYMENT LINK
    # -----------------------------

    elif status == "LINK_GENERATED":

        st.info(
            "🔗 Payment recovery link generated."
        )

        st.code(
            action_result.get(
                "payment_link",
                "No link"
            )
        )


    # -----------------------------
    # HUMAN REVIEW
    # -----------------------------

    elif status == "ESCALATED":

        st.error(
            "🚨 TRANSACTION ESCALATED TO HUMAN REVIEW"
        )

        st.write(
            action_result.get(
                "reason",
                "Suspicious or high-risk transaction."
            )
        )


    # -----------------------------
    # MESSAGE
    # -----------------------------

    elif status == "MESSAGE_SENT":

        st.info(
            "📩 Customer was asked to update their payment method."
        )


    # -----------------------------
    # OTHER
    # -----------------------------

    else:

        st.warning(
            f"Recovery status: {status}"
        )


    # =====================================================
    # ACTIVITY LOG
    # =====================================================

    st.subheader("🔎 Agent Activity")

    activity_log = recovery.get(
        "activity_log",
        []
    )

    for step in activity_log:

        st.write(step)


    # =====================================================
    # TECHNICAL RESPONSE
    # =====================================================

    with st.expander(
        "View Technical Response"
    ):

        st.json(recovery)


# =========================================================
# RECOVERY HISTORY
# =========================================================

st.divider()

st.subheader("📜 Recovery Activity")

if recovery_logs:

    logs_df = pd.DataFrame(
        recovery_logs
    )

    st.dataframe(
        logs_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No recovery activity recorded yet."
    )
from tools import (
    get_transaction,
    get_customer_history,
    get_policy,
    retry_payment,
    generate_payment_link,
    escalate_to_human
)


print("\n--- TRANSACTION ---")
print(get_transaction("TXN1001"))


print("\n--- CUSTOMER ---")
print(get_customer_history("CUST001"))


print("\n--- POLICY ---")
print(get_policy("NETWORK_ERROR"))


print("\n--- PAYMENT RETRY ---")
print(retry_payment("TXN1001"))


print("\n--- PAYMENT LINK ---")
print(generate_payment_link("TXN1002"))


print("\n--- HUMAN ESCALATION ---")
print(
    escalate_to_human(
        "TXN1005",
        "Suspicious transaction detected."
    )
)
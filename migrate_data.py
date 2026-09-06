import json

from db import (
    customers_collection,
    transactions_collection,
    policies_collection,
    recovery_actions_collection
)


# -----------------------------
# LOAD JSON FILE
# -----------------------------

def load_json(filename):

    with open(
        f"data/{filename}",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# -----------------------------
# LOAD DATA
# -----------------------------

customers = load_json("customers.json")
transactions = load_json("transactions.json")
policies = load_json("policies.json")
recovery_logs = load_json("recovery_log.json")


# -----------------------------
# CLEAR OLD DEMO DATA
# -----------------------------

customers_collection.delete_many({})
transactions_collection.delete_many({})
policies_collection.delete_many({})
recovery_actions_collection.delete_many({})


# -----------------------------
# INSERT CUSTOMERS
# -----------------------------

if customers:
    customers_collection.insert_many(customers)

print(
    f"✅ Inserted {len(customers)} customers"
)


# -----------------------------
# INSERT TRANSACTIONS
# -----------------------------

if transactions:
    transactions_collection.insert_many(
        transactions
    )

print(
    f"✅ Inserted {len(transactions)} transactions"
)


# -----------------------------
# INSERT POLICIES
# -----------------------------

if policies:

    policy_documents = []

    for reason, policy in policies.items():

        policy_documents.append({
            "failure_reason": reason,
            "action": policy["action"],
            "description": policy["description"]
        })

    policies_collection.insert_many(
        policy_documents
    )

print(
    f"✅ Inserted {len(policies)} policies"
)


# -----------------------------
# INSERT RECOVERY LOGS
# -----------------------------

if recovery_logs:

    recovery_actions_collection.insert_many(
        recovery_logs
    )

print(
    f"✅ Inserted {len(recovery_logs)} recovery logs"
)


print("\n🎉 Migration completed!")
print("Database: paypilot_db")
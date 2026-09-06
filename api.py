from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

from db import transactions_collection, policies_collection
from agent import analyze_transaction, execute_recovery


app = FastAPI(title="PayPilot Payment API")


# -----------------------------
# Transaction data model
# -----------------------------

class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    payment_method: str
    status: str = "FAILED"
    failure_reason: str | None = None


# -----------------------------
# Home
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "PayPilot Payment API is running"
    }


# -----------------------------
# Create transaction
# -----------------------------

@app.post("/transactions")
def create_transaction(transaction: Transaction):

    transaction_data = transaction.model_dump()

    transaction_data["timestamp"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # 1. Save transaction to MongoDB
    transactions_collection.insert_one(transaction_data)

    # IMPORTANT:
    # MongoDB adds an ObjectId called "_id".
    # Remove it before returning the response.
    transaction_data.pop("_id", None)

    # -----------------------------
    # 2. Analyze failed payment
    # -----------------------------

    ai_result = None
    recovery_result = None

    if transaction_data["status"] == "FAILED":

        ai_result = analyze_transaction(
            transaction_data["transaction_id"]
        )

        # -----------------------------
        # 3. Merchant policy guardrail
        # -----------------------------

        failure_reason = transaction_data["failure_reason"]

        policy = policies_collection.find_one(
            {"failure_reason": failure_reason},
            {"_id": 0}
        )

        if policy:

            policy_action = policy["action"]

            ai_action = ai_result.get(
                "recommended_action"
            )

            # Merchant policy has final authority
            if ai_action != policy_action:

                ai_result["recommended_action"] = policy_action

                ai_result["reason"] = (
                    "AI recommendation was overridden "
                    "by merchant policy."
                )

            # -----------------------------
            # 4. Execute recovery
            # -----------------------------

            recovery_result = execute_recovery(
                transaction_data["transaction_id"],
                policy_action,
                ai_result.get("reason", "")
            )
            # -----------------------------
# Verify recovery result
# -----------------------------

            final_transaction = transactions_collection.find_one(
                {"transaction_id": transaction_data["transaction_id"]},
                {"_id": 0}
            )

            recovery_result["verification"] = {
                "final_status": final_transaction["status"],
                "verified": final_transaction["status"] == "SUCCESS"
            }

    # -----------------------------
    # 5. Return complete result
    # -----------------------------

    return {
        "message": "Transaction processed by PayPilot",
        "transaction": transaction_data,
        "ai_analysis": ai_result,
        "recovery": recovery_result
    }


# -----------------------------
# Get all transactions
# -----------------------------

@app.get("/transactions")
def get_transactions():

    transactions = list(
        transactions_collection.find(
            {},
            {"_id": 0}
        )
    )

    return transactions


# -----------------------------
# Get one transaction
# -----------------------------

@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):

    transaction = transactions_collection.find_one(
        {"transaction_id": transaction_id},
        {"_id": 0}
    )

    if not transaction:

        return {
            "error": "Transaction not found"
        }

    return transaction
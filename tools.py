import random

from db import (
    customers_collection,
    transactions_collection,
    policies_collection,
    recovery_actions_collection
)


# ===================================
# GET TRANSACTION
# ===================================

def get_transaction(transaction_id: str):

    transaction = transactions_collection.find_one(
        {"transaction_id": transaction_id},
        {"_id": 0}
    )

    if transaction:
        return transaction

    return {
        "error": f"Transaction {transaction_id} not found"
    }


# ===================================
# GET CUSTOMER HISTORY
# ===================================

def get_customer_history(customer_id: str):

    customer = customers_collection.find_one(
        {"customer_id": customer_id},
        {"_id": 0}
    )

    if customer:
        return customer

    return {
        "error": f"Customer {customer_id} not found"
    }


# ===================================
# GET MERCHANT POLICY
# ===================================

def get_policy(failure_reason: str):

    policy = policies_collection.find_one(
        {"failure_reason": failure_reason},
        {"_id": 0}
    )

    if policy:
        return policy

    return {
        "error": f"No policy found for {failure_reason}"
    }


# ===================================
# SAVE RECOVERY LOG
# ===================================

def save_recovery_log(
    transaction_id,
    action,
    result
):

    log_entry = {

        "transaction_id": transaction_id,

        "action": action,

        "status": result.get("status"),

        "timestamp": __import__("datetime")
        .datetime.now()
        .strftime("%Y-%m-%d %H:%M:%S")
    }

    recovery_actions_collection.insert_one(
        log_entry
    )


# ===================================
# RETRY PAYMENT
# ===================================

def retry_payment(transaction_id: str):

    transaction = get_transaction(
        transaction_id
    )

    if "error" in transaction:
        return transaction


    # Already successful
    if transaction["status"] == "SUCCESS":

        result = {

            "transaction_id": transaction_id,

            "status": "ALREADY_SUCCESSFUL"
        }

        save_recovery_log(
            transaction_id,
            "RETRY_PAYMENT",
            result
        )

        return result


    # Simulate retry
    success = random.random() < 0.75


    if success:

        # Update MongoDB
        transactions_collection.update_one(
            {
                "transaction_id":
                    transaction_id
            },
            {
                "$set": {
                    "status": "SUCCESS",
                    "failure_reason": None
                }
            }
        )

        result = {

            "transaction_id": transaction_id,

            "status": "SUCCESS",

            "message":
                "Payment successfully recovered."
        }

    else:

        result = {

            "transaction_id": transaction_id,

            "status": "FAILED",

            "message":
                "Payment retry failed."
        }


    save_recovery_log(
        transaction_id,
        "RETRY_PAYMENT",
        result
    )

    return result


# ===================================
# GENERATE PAYMENT LINK
# ===================================

def generate_payment_link(
    transaction_id: str
):

    transaction = get_transaction(
        transaction_id
    )

    if "error" in transaction:
        return transaction


    result = {

        "transaction_id":
            transaction_id,

        "payment_link":
            f"https://paypilot.demo/pay/{transaction_id}",

        "amount":
            transaction["amount"],

        "status":
            "LINK_GENERATED"
    }


    save_recovery_log(
        transaction_id,
        "GENERATE_PAYMENT_LINK",
        result
    )


    return result


# ===================================
# SEND CUSTOMER MESSAGE
# ===================================

def send_customer_message(
    transaction_id: str,
    message: str
):

    transaction = get_transaction(
        transaction_id
    )

    if "error" in transaction:
        return transaction


    result = {

        "transaction_id":
            transaction_id,

        "recipient":
            transaction["customer_id"],

        "status":
            "MESSAGE_SENT",

        "message":
            message
    }


    save_recovery_log(
        transaction_id,
        "SEND_CUSTOMER_MESSAGE",
        result
    )


    return result


# ===================================
# ESCALATE TO HUMAN
# ===================================

def escalate_to_human(
    transaction_id: str,
    reason: str
):

    result = {

        "transaction_id":
            transaction_id,

        "status":
            "ESCALATED",

        "reason":
            reason,

        "message":
            "Transaction has been sent for human review."
    }


    save_recovery_log(
        transaction_id,
        "ESCALATE_TO_HUMAN",
        result
    )


    return result
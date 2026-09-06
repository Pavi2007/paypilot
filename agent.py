from openai import OpenAI
from dotenv import load_dotenv
import os
import json

from tools import (
    get_transaction,
    get_customer_history,
    get_policy,
    retry_payment,
    generate_payment_link,
    send_customer_message,
    escalate_to_human
)


# ===================================
# OPENAI SETUP
# ===================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ===================================
# ANALYZE TRANSACTION
# ===================================

def analyze_transaction(transaction_id):

    activity_log = []


    def log(message):

        activity_log.append(message)


    # -----------------------------------
    # GET TRANSACTION
    # -----------------------------------

    log(
        f"🔍 Retrieving transaction {transaction_id}"
    )

    transaction = get_transaction(
        transaction_id
    )


    if "error" in transaction:

        return transaction


    # -----------------------------------
    # GET CUSTOMER
    # -----------------------------------

    log(
        f"👤 Retrieving customer "
        f"{transaction['customer_id']}"
    )

    customer = get_customer_history(
        transaction["customer_id"]
    )


    # -----------------------------------
    # GET POLICY
    # -----------------------------------

    log(
        f"📜 Checking policy for "
        f"{transaction['failure_reason']}"
    )

    policy = get_policy(
        transaction["failure_reason"]
    )


    # -----------------------------------
    # AI ANALYSIS
    # -----------------------------------

    log(
        "🧠 AI is analyzing the transaction"
    )


    prompt = f"""
You are PayPilot, an AI payment operations agent.

Your job is to analyze a failed payment
and recommend the safest recovery action.

TRANSACTION:
{json.dumps(transaction, indent=2)}

CUSTOMER:
{json.dumps(customer, indent=2)}

MERCHANT POLICY:
{json.dumps(policy, indent=2)}

Return ONLY valid JSON:

{{
    "transaction_id": "{transaction_id}",
    "analysis": "...",
    "risk_level": "LOW/MEDIUM/HIGH",
    "recommended_action": "RETRY_PAYMENT/GENERATE_PAYMENT_LINK/UPDATE_PAYMENT_METHOD/SEND_PAYMENT_LINK/ESCALATE_TO_HUMAN",
    "reason": "..."
}}

Rules:

1. Always follow the merchant policy.
2. Never recommend retrying suspicious transactions.
3. Consider customer payment history.
4. Keep the analysis concise.
"""


    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )


    result = response.output_text


    # -----------------------------------
    # PARSE AI RESPONSE
    # -----------------------------------

    try:

        decision = json.loads(result)

    except json.JSONDecodeError:

        return {

            "transaction_id":
                transaction_id,

            "analysis":
                result,

            "risk_level":
                "UNKNOWN",

            "recommended_action":
                "MANUAL_REVIEW",

            "reason":
                "AI response was not valid JSON.",

            "action_result":
                {},

            "activity_log":
                activity_log
        }


    # -----------------------------------
    # STORE DECISION
    # -----------------------------------

    action = decision.get(
        "recommended_action",
        "MANUAL_REVIEW"
    )


    log(
        f"⚡ AI recommendation: {action}"
    )


    # IMPORTANT:
    # We DO NOT execute the action here.
    #
    # The dashboard will show the AI decision
    # first, and the merchant can then click
    # "Execute Recovery".


    decision["action_result"] = {}

    decision["activity_log"] = activity_log

    return decision


# ===================================
# EXECUTE RECOVERY
# ===================================

def execute_recovery(
    transaction_id,
    action,
    reason=""
):

    activity_log = []


    def log(message):

        activity_log.append(message)


    log(
        f"⚡ Executing recovery action: {action}"
    )


    # ===================================
    # RETRY PAYMENT
    # ===================================

    if action == "RETRY_PAYMENT":

        log(
            "💳 Attempting payment retry"
        )


        action_result = retry_payment(
            transaction_id
        )


        # -----------------------------------
        # RETRY SUCCESS
        # -----------------------------------

        if action_result.get("status") == "SUCCESS":

            log(
                "✅ Payment successfully recovered"
            )


        # -----------------------------------
        # RETRY FAILED → FALLBACK
        # -----------------------------------

        elif action_result.get("status") == "FAILED":

            log(
                "❌ Payment retry failed"
            )

            log(
                "🔄 Starting fallback recovery"
            )


            # Generate payment link

            log(
                "🔗 Generating alternative payment link"
            )


            fallback_result = generate_payment_link(
                transaction_id
            )


            # Send customer message

            if fallback_result.get(
                "status"
            ) == "LINK_GENERATED":

                log(
                    "📩 Sending recovery message"
                )


                message_result = send_customer_message(

                    transaction_id,

                    "Your payment could not be completed. "
                    "Please use the recovery payment link "
                    "to complete your payment."
                )


                action_result = {

                    "status":
                        "FALLBACK_RECOVERY",

                    "initial_action":
                        "RETRY_PAYMENT",

                    "initial_result":
                        "FAILED",

                    "fallback_action":
                        "GENERATE_PAYMENT_LINK",

                    "payment_link":
                        fallback_result[
                            "payment_link"
                        ],

                    "message_status":
                        message_result[
                            "status"
                        ]
                }


                log(
                    "✅ Fallback recovery completed"
                )


    # ===================================
    # GENERATE PAYMENT LINK
    # ===================================

    elif action in [

        "GENERATE_PAYMENT_LINK",

        "SEND_PAYMENT_LINK"

    ]:

        log(
            "🔗 Generating payment link"
        )


        action_result = generate_payment_link(
            transaction_id
        )


        if action_result.get(
            "status"
        ) == "LINK_GENERATED":

            log(
                "📩 Payment recovery link ready"
            )


    # ===================================
    # UPDATE PAYMENT METHOD
    # ===================================

    elif action == "UPDATE_PAYMENT_METHOD":

        log(
            "📩 Asking customer to update "
            "payment method"
        )


        action_result = send_customer_message(

            transaction_id,

            "Please update your payment method "
            "to complete the payment."
        )


    # ===================================
    # HUMAN REVIEW
    # ===================================

    elif action == "ESCALATE_TO_HUMAN":

        log(
            "🚨 Escalating transaction "
            "to human review"
        )


        action_result = escalate_to_human(

            transaction_id,

            reason
        )


    # ===================================
    # UNKNOWN ACTION
    # ===================================

    else:

        log(
            "⚠️ No automated action performed"
        )


        action_result = {

            "status":
                "NO_ACTION",

            "message":
                "No automated action was performed."
        }


    # -----------------------------------
    # RETURN RESULT
    # -----------------------------------

    return {

        "transaction_id":
            transaction_id,

        "action":
            action,

        "action_result":
            action_result,

        "activity_log":
            activity_log
    }


# ===================================
# TEST
# ===================================

if __name__ == "__main__":

    transaction_id = "TXN1001"


    # First analyze

    decision = analyze_transaction(
        transaction_id
    )


    print(
        "\n========== PAYPILOT AI ==========\n"
    )


    print(
        json.dumps(
            decision,
            indent=2
        )
    )


    # IMPORTANT:
    # Recovery is NOT automatically executed.
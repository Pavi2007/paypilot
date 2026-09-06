from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")

# PayPilot database
db = client["paypilot_db"]

# Collections
customers_collection = db["customers"]
transactions_collection = db["transactions"]
policies_collection = db["policies"]
recovery_actions_collection = db["recovery_actions"]

print("✅ Connected to MongoDB")
print("Database:", db.name)
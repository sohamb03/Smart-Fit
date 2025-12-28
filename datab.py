from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Use environment variables for security
db = client["user_auth_db"]
users_collection = db["users"]

def insert_user(username, email, password):
    """Insert a new user into the users collection."""
    users_collection.insert_one({
        "username": username,
        "email": email,
        "password": password
    })

def find_user_by_email(email):
    """Find a user by email."""
    return users_collection.find_one({"email": email})

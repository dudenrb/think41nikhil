# backend/load_data.py
import pandas as pd
from pymongo import MongoClient
import os
import json # To pretty-print JSON for debugging

# --- Configuration ---
# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/" # Default URI for local MongoDB
DB_NAME = "ecommerce_chatbot_db"       # Name of your database

# Path to your CSV files (relative to this script's location)
# Assumes CSVs are in a 'data' directory directly under 'backend'
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Mapping of CSV file names to MongoDB collection names
# Each CSV file will be loaded into its corresponding collection.
CSV_COLLECTION_MAP = {
    "distribution_centers.csv": "distribution_centers",
    "inventory_items.csv": "inventory_items",
    "order_items.csv": "order_items",
    "orders.csv": "orders",
    "products.csv": "products",
    "users.csv": "users",
}

# --- Main Ingestion Function ---
def load_csv_to_mongodb():
    """
    Connects to MongoDB, reads each specified CSV file from the DATA_DIR,
    and inserts its data into the corresponding MongoDB collection.
    It clears the collection before insertion to ensure a fresh load.
    """
    client = None # Initialize client to None
    try:
        # Establish a connection to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME] # Access the specified database

        # Ping the database to confirm connection
        client.admin.command('ping')
        print(f"Successfully connected to MongoDB server at {MONGO_URI} and accessing database '{DB_NAME}'.")

        # Iterate through each CSV file and its target collection
        for csv_file, collection_name in CSV_COLLECTION_MAP.items():
            file_path = os.path.join(DATA_DIR, csv_file)

            # Check if the CSV file exists
            if not os.path.exists(file_path):
                print(f"Warning: CSV file '{csv_file}' not found at '{file_path}'. Skipping this file.")
                continue

            print(f"\n--- Processing '{csv_file}' into collection '{collection_name}' ---")
            try:
                # Read CSV into a pandas DataFrame
                # pandas is great for handling various CSV quirks automatically
                df = pd.read_csv(file_path)

                # Convert DataFrame to a list of dictionaries.
                # Each dictionary will be a document in MongoDB.
                records = df.to_dict(orient='records')

                # Access the target collection
                collection = db[collection_name]

                # Optional: Clear existing data in the collection
                # This ensures that each run of the script results in a fresh dataset
                # without duplicate entries from previous runs.
                delete_result = collection.delete_many({})
                print(f"Cleared {delete_result.deleted_count} existing documents from '{collection_name}'.")

                # Insert the records into the collection
                if records:
                    insert_result = collection.insert_many(records)
                    print(f"Successfully inserted {len(insert_result.inserted_ids)} documents into '{collection_name}'.")

                    # Optional: Print the first inserted document for verification
                    if len(records) > 0:
                        print("Sample document from collection:")
                        # Retrieve and print one document to show successful ingestion
                        sample_doc = collection.find_one({})
                        # Remove MongoDB's internal _id for cleaner printing if desired
                        if sample_doc and '_id' in sample_doc:
                            sample_doc['_id'] = str(sample_doc['_id']) # Convert ObjectId to string for printing
                        print(json.dumps(sample_doc, indent=2))
                else:
                    print(f"No records found in '{csv_file}' to insert. Collection '{collection_name}' remains empty.")

            except pd.errors.EmptyDataError:
                print(f"Error: '{csv_file}' is empty. No data to load for collection '{collection_name}'.")
            except FileNotFoundError:
                print(f"Error: '{csv_file}' not found at '{file_path}'. Please ensure it exists.")
            except Exception as e:
                print(f"An error occurred while loading '{csv_file}' into '{collection_name}': {e}")

    except Exception as e:
        print(f"Could not connect to MongoDB or a fatal error occurred: {e}")
    finally:
        # Ensure the MongoDB client connection is closed
        if client:
            client.close()
            print("\nMongoDB connection closed.")

# --- Script Entry Point ---
if __name__ == "__main__":
    # Check if the 'data' directory exists and prompt if not
    if not os.path.exists(DATA_DIR):
        print(f"Error: The 'data' directory was not found at '{DATA_DIR}'.")
        print("Please ensure you have created a 'data' folder inside your 'backend' directory")
        print("and placed all the dataset CSV files inside it.")
        print("You can download the dataset from: https://github.com/recruit41/ecommerce-dataset")
        # Optionally create the directory, though user still needs to place files
        # os.makedirs(DATA_DIR, exist_ok=True)
    else:
        load_csv_to_mongodb()
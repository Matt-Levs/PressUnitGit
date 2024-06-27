import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests
import time

def initialize_firebase():
        online = False
        while not online:
            try:
                # Check for internet connection
                requests.get('https://www.google.com', timeout=5)
                online = True
                # Use a service account.
                cred = credentials.Certificate('operationsview-56393-firebase-adminsdk-1j3ek-162c24ab9d.json')
                firebase_admin.initialize_app(cred)
                return firestore.client()
            except (requests.ConnectionError, requests.Timeout):
                print("No internet connection. Firebase not initialized.")
                time.sleep(15)
            except Exception as e:
                print(f"An error occurred: {e}")
                return None

db = initialize_firebase()

def send_data(data, location, equipment):
    if db is None:
        print("No connection to Firebase. Data not sent.")
        return
    
    try:
        db.collection(location).document(equipment).collection('data').add(data)
        print("Data sent successfully.")
    except Exception as e:
        print(f"An error occurred while sending data: {e}")

# Example usage:
# send_data({"example_field": "example_value"}, "location_example", "equipment_example")

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
        print(location)
        print(equipment)
        db.collection(location).document(equipment).collection('data').add(data)
        print("Data sent successfully.")
    except Exception as e:
        print(f"An error occurred while sending data: {e}")



def check_or_create_device(device_name):
    if db is None:
        print("No connection to Firebase. Cannot check or create device.")
        return
    
    devices_collection = db.collection('Devices')
    device_doc = devices_collection.document(device_name)
    
    try:
        # Try to get the document
        doc = device_doc.get()

        if doc.exists:
            # Document exists, return unit_location and unit_equipment
            unit_location = doc.to_dict().get('unit_location', 'N/A')
            unit_equipment = doc.to_dict().get('unit_equipment', 'N/A')
            unit_timezone = doc.to_dict().get('unit_timezone', 'N/A')
            print(f"Device found. Location: {unit_location}, Equipment: {unit_equipment}, Timezone: {unit_timezone}")
            return unit_location, unit_equipment, unit_timezone
        else:
            # Document does not exist, create a new one with default values
            device_doc.set({
                'unit_location': 'default',
                'unit_equipment': 'default',
                'unit_timezone': 'US/Eastern',
            })
            print("Device not found. Created new device with default values.")
            return 'default', 'default', 'US/Eastern'
    
    except Exception as e:
        print(f"An error occurred while checking/creating device: {e}")
        return None

import os
import re

import threading
import time
from datetime import datetime, timedelta
from pytz import timezone
from gpiozero import Button

import PressDataframeV5RPI as PD
import DatabaseV3RPI as DDb

# Constants
MACHINE_OFF_CUTOFF = 10  # Time in seconds to consider the machine off
UPDATE_INTERVAL = 30     # Time in seconds to update data
UNIT_LOCATION = ''
UNIT_EQUIPMENT = ''

button = Button(6, bounce_time=None, pull_up=False)

def press_down():
    global equip_history, last_stomp_time
    print('HIT')
    last_stomp_time = datetime.now(UNIT_TIMEZONE)
    equip_history = PD.press_hit(equip_history, last_stomp_time)

button.when_pressed = press_down

def get_mac_address():
    try:
        # Run the ifconfig command and capture the output
        ifconfig_output = os.popen('ifconfig').read()

        # Use regex to find the MAC address (format: XX:XX:XX:XX:XX:XX)
        mac_address = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', ifconfig_output).group()

        return mac_address
    except Exception as e:
        print(f"Error retrieving MAC address: {e}")
        return None

mac = get_mac_address()
if mac:
    print(f"The MAC address is: {mac}")
    UNIT_LOCATION, UNIT_EQUIPMENT, timezone_text = DDb.check_or_create_device(mac)
    UNIT_TIMEZONE = timezone('US/Eastern')
    last_stomp_time = datetime.now(UNIT_TIMEZONE)
    last_upload_time = datetime.now(UNIT_TIMEZONE)

else:
    UNIT_LOCATION = 'Default'
    UNIT_EQUIPMENT = 'Defualt'
    UNIT_TIMEZONE = timezone('US/Eastern')
    last_stomp_time = datetime.now(UNIT_TIMEZONE)
    last_upload_time = datetime.now(UNIT_TIMEZONE)
    print("MAC address could not be found.")

equip_history = PD.create_history()

while True:
    current_time = datetime.now(UNIT_TIMEZONE)
    try:
        new_data = equip_history[-1]
    except:
        new_data = None

    if (current_time - last_stomp_time) > timedelta(seconds=MACHINE_OFF_CUTOFF):
        print('Press Down Delta ', current_time - last_stomp_time)
        equip_history = PD.press_down(equip_history, current_time)

    if (current_time - last_upload_time) > timedelta(seconds=UPDATE_INTERVAL):
        DDb.send_data(new_data, UNIT_LOCATION, UNIT_EQUIPMENT)
        last_upload_time = current_time

    time.sleep(UPDATE_INTERVAL)  # Sleep for the update interval before checking again
    print('Update')

# Start the background thread
update_thread = threading.Thread(target=periodic_update, daemon=True)
update_thread.start()

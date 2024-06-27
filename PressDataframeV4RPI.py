from collections import deque
from datetime import datetime, timedelta, timezone

# Constants
SHORT_SPM_DURATION = timedelta(minutes=2)
LONG_SPM_DURATION = timedelta(hours=1)
LONG_DOWNTIME_DURATION = timedelta(hours=3)
MAX_HISTORY_LENGTH = LONG_DOWNTIME_DURATION.total_seconds()  # Max length for 3 hours in seconds


# Initialize deque
def create_history():
    return deque()

# Helper function to trim history based on time window
def trim_history(history, current_timestamp):
    global LONG_DOWNTIME_DURATION
    cutoff_time = current_timestamp - LONG_DOWNTIME_DURATION
    while history and history[0]['timestamp'] < cutoff_time:
        history.popleft()

# Function to calculate short spm
def calculate_short_spm(history, current_timestamp):
    trim_history(history, current_timestamp)
    short_spm_count = [record for record in history if not record['press_off'] and record['timestamp']>current_timestamp-SHORT_SPM_DURATION]
    
    if not short_spm_count:
        return 0

    elapsed_time = current_timestamp - short_spm_count[0]['timestamp']

    if elapsed_time < SHORT_SPM_DURATION:
        short_spm = len(short_spm_count) / elapsed_time.total_seconds() * 60
    else:
        short_spm = len(short_spm_count) / SHORT_SPM_DURATION.total_seconds() * 60
    print('Short SPM: ', short_spm)
    return short_spm

# Function to calculate long spm
def calculate_long_spm(history, current_timestamp):
    trim_history(history, current_timestamp)
    long_spm_count = [record for record in history if not record['press_off']and record['timestamp']>current_timestamp-LONG_SPM_DURATION]

    if not long_spm_count:
        return 0

    elapsed_time = current_timestamp - long_spm_count[0]['timestamp']

    if elapsed_time < LONG_SPM_DURATION:
        long_spm = len(long_spm_count) / elapsed_time.total_seconds() * 60
    else:
        long_spm = len(long_spm_count) / LONG_SPM_DURATION.total_seconds() * 60
    print('Long SPM', long_spm)
    return long_spm

# Function to update current downtime and long downtime
def update_downtimes(history, current_timestamp, current_press_down):
    if not history:
        return 0, 0

    last_record = history[-1]

    # Calculate current downtime
    if last_record['press_off'] and current_press_down:
        current_downtime = last_record['current_downtime'] + (current_timestamp - last_record['timestamp']).total_seconds()
    elif not last_record['press_off'] and current_press_down:
        current_downtime = 0
    else:
        current_downtime = last_record['current_downtime']

    
    last_dowtime_total = history[-1]['long_downtime']
    if history[-1]['press_off']==True and current_press_down == True:
        long_downtime = last_dowtime_total + (current_downtime - history[-1]['current_downtime'])
    else:
        long_downtime = history[-1]['long_downtime']

    return current_downtime, long_downtime

# Function to handle press_hit
def press_hit(history, current_timestamp):
    short_spm = calculate_short_spm(history, current_timestamp)
    long_spm = calculate_long_spm(history, current_timestamp)
    current_downtime, long_downtime = update_downtimes(history, current_timestamp, False)
    
    new_record = {
        'timestamp': current_timestamp,
        'short_spm': short_spm,
        'long_spm': long_spm,
        'press_off': False,
        'last_down': history[-1]['last_down'] if history else 0,
        'current_downtime': current_downtime,
        'long_downtime': long_downtime
    }
    history.append(new_record)
    return history

# Function to handle press_down
def press_down(history, current_timestamp):
    current_downtime, long_downtime = update_downtimes(history, current_timestamp, True)
    
    new_record = {
        'timestamp': current_timestamp,
        'short_spm': 0,
        'long_spm': history[-1]['long_spm'] if history else 0,
        'press_off': True,
        'last_down': current_timestamp if not history or not history[-1]['press_off'] else history[-1]['last_down'],
        'current_downtime': current_downtime,
        'long_downtime': long_downtime
    }
    history.append(new_record)
    return history

# Example usage
if __name__ == "__main__":
    current_time = datetime.now(timezone.utc)
    state_history = create_history()
    state_history = press_down(state_history, current_time)
    state_history = press_hit(state_history, current_time + timedelta(seconds=10))
    state_history = press_hit(state_history, current_time + timedelta(seconds=20))
    state_history = press_down(state_history, current_time + timedelta(seconds=30))
    state_history = press_hit(state_history, current_time + timedelta(seconds=40))
    state_history = press_hit(state_history, current_time + timedelta(seconds=50))
    state_history = press_down(state_history, current_time + timedelta(seconds=60))
    state_history = press_down(state_history, current_time + timedelta(seconds=70))
    state_history = press_hit(state_history, current_time + timedelta(seconds=80))
    state_history = press_hit(state_history, current_time + timedelta(seconds=90))
    state_history = press_down(state_history, current_time + timedelta(seconds=100))
    state_history = press_down(state_history, current_time + timedelta(seconds=110))
    state_history = press_down(state_history, current_time + timedelta(seconds=120))
    state_history = press_hit(state_history, current_time + timedelta(seconds=130))
    state_history = press_hit(state_history, current_time + timedelta(seconds=140))

    print("Final History")

    # Print the state history
    for record in state_history:
        print(record)

from collections import deque
from datetime import datetime, timedelta, timezone

# Set your timezone here (e.g., UTC, or any other timezone)
TIMEZONE = timezone(timedelta(hours=-5))  # Replace this with the desired timezone

# Constants
SHORT_SPM_DURATION = timedelta(minutes=0.5)
LONG_SPM_DURATION = timedelta(hours=0.016)
LONG_DOWNTIME_DURATION = timedelta(hours=0.016)
MAX_HISTORY_LENGTH = LONG_DOWNTIME_DURATION.total_seconds()  # Max length for 3 hours in seconds
downtime_total = 0

# Initialize deque
def create_history():
    return deque()

def trim_history(history, current_timestamp):
    global downtime_total
    
    # Ensure the current_timestamp is aware of the set timezone
    current_timestamp = current_timestamp.astimezone(TIMEZONE)

    # Get the start of the current day (midnight) in the correct timezone
    start_of_today = datetime(current_timestamp.year, current_timestamp.month, current_timestamp.day, tzinfo=TIMEZONE)
    
    while history and history[0]['timestamp'] < start_of_today:
        remove_downtime = history[1]['current_downtime'] - history[0]['current_downtime']
        if remove_downtime > 0:
            downtime_total -= remove_downtime
        history.popleft()

def calculate_num_hits(history):
    count = 1
    for record in history:
        if not record['press_off']:
            count += 1
    return count

# Function to calculate short spm
def calculate_short_spm(history, current_timestamp):
    # Ensure the current_timestamp is aware of the set timezone
    current_timestamp = current_timestamp.astimezone(TIMEZONE)

    # Check if the history is empty or if the last record has press_off as True
    if not history or history[-1]['press_off']:
        return 0
    
    # Get the timestamp of the last record
    last_record_timestamp = history[-1]['timestamp']
    
    # Calculate the elapsed time from the last record to the current timestamp
    elapsed_time = current_timestamp - last_record_timestamp

    # Calculate short SPM based on the elapsed time
    short_spm = 1 / elapsed_time.total_seconds() * 60
    
    print('Short SPM: ', short_spm)
    return short_spm

# Function to calculate long spm
def calculate_long_spm(history, current_timestamp):
    # Ensure the current_timestamp is aware of the set timezone
    current_timestamp = current_timestamp.astimezone(TIMEZONE)

    # Filter records where short_spm is not 0
    valid_spm_records = [record for record in history if not record['press_off'] and record['short_spm'] > 0]

    if not valid_spm_records:
        return 0

    # Calculate the average short_spm
    total_spm = sum(record['short_spm'] for record in valid_spm_records)
    average_spm = total_spm / len(valid_spm_records)

    print('Long SPM:', average_spm)
    return average_spm

# Function to update current downtime and long downtime
def update_downtimes(history, current_timestamp, current_press_down):
    global downtime_total

    # Ensure the current_timestamp is aware of the set timezone
    current_timestamp = current_timestamp.astimezone(TIMEZONE)

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

    if last_record['press_off'] == True and current_press_down == True:
        downtime_total = downtime_total + (current_downtime - history[-1]['current_downtime'])

    print(downtime_total)
    return current_downtime, downtime_total

# Function to handle press_hit
def press_hit(history, current_timestamp):
    # Ensure the current_timestamp is aware of the set timezone
    current_timestamp = current_timestamp.astimezone(TIMEZONE)
    
    trim_history(history, current_timestamp)
    num_hits = calculate_num_hits(history)
    short_spm = calculate_short_spm(history, current_timestamp)
    long_spm = calculate_long_spm(history, current_timestamp)
    current_downtime, long_downtime = update_downtimes(history, current_timestamp, False)
    
    new_record = {
        'timestamp': current_timestamp,
        'num_hits': num_hits,
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
    # Ensure the current_timestamp is aware of the set timezone
    current_timestamp = current_timestamp.astimezone(TIMEZONE)
    trim_history(history, current_timestamp)
    num_hits = calculate_num_hits(history)
    current_downtime, long_downtime = update_downtimes(history, current_timestamp, True)
    
    new_record = {
        'timestamp': current_timestamp,
        'num_hits': num_hits,
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
    current_time = datetime.now(TIMEZONE)
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

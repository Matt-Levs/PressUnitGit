import threading
import time
from datetime import datetime, timedelta
from pytz import timezone
from gpiozero import Button

import dash
from dash.dependencies import Input, Output
import plotly.graph_objs as go

import PressDataframeV4RPI as PD
import DatabaseV2RPI as DDb

#TEST
# Constants
MACHINE_OFF_CUTOFF = 10  # Time in seconds to consider the machine off
UPDATE_INTERVAL = 20     # Time in seconds to update data
UNIT_LOCATION = 'Mural'
UNIT_EQUIPMENT = 'Press_Test'
UNIT_TIMEZONE = timezone('US/Eastern')
last_stomp_time = datetime.now(UNIT_TIMEZONE)
last_upload_time = datetime.now(UNIT_TIMEZONE)

equip_history = PD.create_history()

button = Button(6, bounce_time=0.1, pull_up=False)


def press_down():
    global equip_history, last_stomp_time
    print('HIT')
    last_stomp_time = datetime.now(UNIT_TIMEZONE)
    equip_history = PD.press_hit(equip_history, last_stomp_time)

button.when_pressed = press_down

def periodic_update():
    global equip_history, last_stomp_time, last_upload_time, UNIT_TIMEZONE, MACHINE_OFF_CUTOFF, UPDATE_INTERVAL
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

# Start the background thread
update_thread = threading.Thread(target=periodic_update, daemon=True)
update_thread.start()

# Initialize Dash app
app_dash = dash.Dash(__name__)

# Define layout
app_dash.layout = dash.html.Div(style={'textAlign': 'center', 'backgroundColor': '#f9f9f9'}, children=[
    dash.html.Div(id="spm", style={'fontSize': '40px', 'color': '#007BFF'}),
    dash.html.Div(id="average-window", style={'fontSize': '24px', 'color': '#666'}),
    dash.html.Div(id="press-down", style={'fontSize': '32px'}),
    dash.dcc.Graph(id='spm-graph', animate=False),
    dash.dcc.Interval(id='interval-component', interval=1*1000),  # Add Interval component to update
    dash.html.Div(id='dummy-div', style={'display': 'none'})  # Dummy div for callback triggering
])

@app_dash.callback(
    [Output('spm', 'children'),
     Output('average-window', 'children'),
     Output('press-down', 'children'),
     Output('spm-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """
    Update the dashboard with the latest data.
    """
    global equip_history, last_stomp_time, UNIT_TIMEZONE, MACHINE_OFF_CUTOFF, UPDATE_INTERVAL
    
    current_time = datetime.now(UNIT_TIMEZONE)
    try:
        new_data = equip_history[-1]
    except:
        new_data = None

    # Update SPM and Press Down information
    spm_element = dash.html.Div(f"Average SPM: {round(new_data['long_spm'], 1)}", style={'fontSize': '40px', 'color': '#007BFF'})
    
    # Convert PD.LONG_SPM_DURATION to decimal hours
    long_spm_duration_hours = PD.LONG_SPM_DURATION.total_seconds() / 3600
    average_window_element = dash.html.Div(f"Average SPM over the last {long_spm_duration_hours:.0f} hours", style={'fontSize': '24px', 'color': '#666'})
    
    if new_data['press_off']:
        heading_text = dash.html.Span("Equipment Down ", style={'color': 'red'})
        duration_text = f"Duration: {round(new_data['current_downtime'] / 60, 2)} mins"
        
        # Check if new_data['last_down'] is 0 or a datetime object and format accordingly
        if new_data['last_down'] == 0:
            last_down_formatted = "0"
        else:
            last_down_formatted = new_data['last_down'].strftime('%Y-%m-%d %H:%M')
        
        last_down_text = f"Last Time Running: {last_down_formatted}"
    else:
        heading_text = dash.html.Span("Running ", style={'color': 'green'})
        duration_text = ''
        
        # Check if new_data['last_down'] is 0 or a datetime object and format accordingly
        if new_data['last_down'] == 0:
            last_down_formatted = "0"
        else:
            last_down_formatted = new_data['last_down'].strftime('%Y-%m-%d %H:%M')
        
        last_down_text = f"Last Time Down: {last_down_formatted} Duration: {round(new_data['current_downtime'] / 60, 2)}"

    press_down_element = dash.html.Div([
        dash.html.H2([heading_text, duration_text], style={'fontSize': '32px'}),
        dash.html.P(last_down_text, style={'fontSize': '24px'})
    ])

    # Update graph
    short_spm = [record['short_spm'] for record in equip_history]
    long_spm = [record['long_spm'] for record in equip_history]
    timestamps = [record['timestamp'] for record in equip_history]

    spm_graph = {
        'data': [
            go.Scatter(
                x=timestamps,
                y=short_spm,
                mode='lines+markers',
                name='Short SPM',
                marker=dict(size=10),
                line=dict(width=3)
            ),
            go.Scatter(
                x=timestamps,
                y=long_spm,
                mode='lines+markers',
                name='Long SPM',
                marker=dict(size=10),
                line=dict(width=3)
            )
        ],
        'layout': go.Layout(
            title='SPM over Time',
            xaxis=dict(title='Time', titlefont=dict(size=18)),
            yaxis=dict(title='SPM', titlefont=dict(size=18)),
            titlefont=dict(size=24)
        )
    }

    return spm_element, average_window_element, press_down_element, spm_graph

if __name__ == "__main__":
    app_dash.run_server(debug=True, use_reloader=False)

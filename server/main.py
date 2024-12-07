import eventlet
eventlet.monkey_patch()  # This must be called before any other imports
import os
import copy
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import csv

# Global variables
app = Flask(__name__)  # Flask app instance
socketio = SocketIO(app)
stations_data = []
last_read_values = {}
items_data_dict = {}
# AQI thresholds
minimum_aqi = 0
good_aqi_high = 50
normal_aqi_high = 100
bad_aqi_high = 250
maximum_aqi = 500


# Function to read station data from a CSV file
def load_stations_data(file_path):
    global stations_data
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            stations_data.append({
                'Station code': row['Station code'],
                'Station name': row['Station name(district)'],
                'Address': row['Address'],
                'Latitude': float(row['Latitude']),
                'Longitude': float(row['Longitude'])
            })
    print('Station data loaded successfully.')
    print(stations_data)


def load_item_data(file_path):
    global items_data_dict
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item_name = row['Item name']
            items_data_dict[item_name] = {
                'Good': float(row['Good(Blue)']),
                'Normal': float(row['Normal(Green)']),
                'Bad': float(row['Bad(Yellow)']),
                'Very bad': float(row['Very bad(Red)'])
            }
    print('Item data loaded successfully.')
    print(items_data_dict)


# Calculates aqi for a certain pollutant
def calculate_aqi(item_name, concentration):
    # Ensure pollutant exists in the item_data_dict
    if item_name not in items_data_dict:
        return None  # Pollutant data not found

    # Fetch the breakpoint values for the pollutant
    breakpoints = items_data_dict[item_name]
    good_concentration_high = breakpoints['Good']
    normal_concentration_high = breakpoints['Normal']
    bad_concentration_high = breakpoints['Bad']
    very_bad_concentration_high = breakpoints['Very bad']

    # Determine the AQI category based on concentration
    if concentration <= good_concentration_high:  # AQI range for "Good"
        index_low = minimum_aqi
        index_high = good_aqi_high
        concentration_low = 0
        concentration_high = good_concentration_high
    elif concentration <= normal_concentration_high:  # AQI range for "Moderate"
        index_low = good_aqi_high + 1
        index_high = normal_aqi_high
        concentration_low = good_concentration_high
        concentration_high = normal_concentration_high
    elif concentration <= bad_concentration_high:  # AQI range for "Unhealthy"
        index_low = normal_aqi_high + 1
        index_high = bad_aqi_high
        concentration_low = normal_concentration_high
        concentration_high = bad_concentration_high
    elif concentration <= very_bad_concentration_high:
        index_low = bad_aqi_high + 1
        index_high = maximum_aqi
        concentration_low = bad_concentration_high
        concentration_high = very_bad_concentration_high
    else:
        print('Concentration exceeds tha maximum concentration')
        exit(1)

    # Apply the linear interpolation formula to calculate the AQI
    aqi = (((concentration - concentration_low) * (index_high - index_low)) / (concentration_high - concentration_low)
           + index_low)

    if aqi > maximum_aqi:
        print('AQI exceeds maximum AQI possible')
        exit(1)

    return int(aqi + 0.5)  # Round to first integer


def get_aqi_color(aqi):
    if aqi <= good_aqi_high:
        color = 'LightBlue'
    elif aqi <= normal_aqi_high:
        color = 'LightGreen'
    elif aqi <= bad_aqi_high:
        color = 'Yellow'
    elif aqi <= maximum_aqi:
        color = 'Red'
    else:
        color = 'undefined color'
    return color


def calculate_aqi_for_all(station_data_dict):
    new_station_data_dict = copy.deepcopy(station_data_dict)
    sensors_data_dict = new_station_data_dict['Sensors data']
    items = sensors_data_dict.keys()

    for item_name in items:
        concentration = sensors_data_dict[item_name]['Value']
        aqi = calculate_aqi(item_name, concentration)
        color = get_aqi_color(aqi)
        new_station_data_dict['Sensors data'][item_name]['AQI'] = aqi
        new_station_data_dict['Sensors data'][item_name]['Color'] = color
    return new_station_data_dict


# Endpoints
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/stations', methods=['GET'])
def get_stations():
    return jsonify(stations_data)


@app.route('/last_read_values', methods=['GET'])
def get_last_read_values():
    return jsonify(last_read_values)


# Receive data from the POST request and forward it to WebSocket clients
@app.route('/data', methods=['POST'])
def receive_data():
    try:
        # Get JSON data from the POST request (from the gateway) and deserializes the JSON
        data_dict = request.get_json()

        # Check that json_data is a valid dictionary
        if not isinstance(data_dict, dict):
            raise ValueError('Invalid data format')
    except Exception as e:
        print(f'Error receiving data: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to receive data'}), 500

    # Log the received data for debugging
    print(f'Received data: {data_dict}')

    aqi_dict = calculate_aqi_for_all(data_dict)

    # Send the processed data to the client using WebSocket
    try:
        socketio.emit('update_station_data', aqi_dict)
        print(f'Data forwarded: {aqi_dict}')
    except Exception as e:
        print(f'Error forwarding data: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to forward data'}), 500

    station_code = aqi_dict['Station code']
    global last_read_values
    last_read_values[station_code] = aqi_dict['Sensors data']

    # Return a successful response to the gateway
    return jsonify({'status': 'success', 'message': 'Data received and forwarded to client'}), 200


# SocketIO event for client connection
@socketio.on('connect')
def handle_connect():
    client_ip = request.remote_addr
    client_port = request.environ.get('REMOTE_PORT')
    print(f'Client connected from {client_ip}:{client_port}')


# SocketIO event for client disconnection
@socketio.on('disconnect')
def handle_disconnect():
    client_ip = request.remote_addr
    client_port = request.environ.get('REMOTE_PORT')
    print(f'Client disconnected from {client_ip}:{client_port}')


def main():
    # Load stations data (id, name, locations)
    base_path = os.path.abspath(os.path.dirname(__file__))
    stations_data_file_path = os.path.join(base_path, 'data', 'Measurement_station_info.csv')
    items_data_file_path = os.path.join(base_path, 'data', 'Measurement_item_info.csv')
    load_stations_data(stations_data_file_path)
    load_item_data(items_data_file_path)
    # Run Flask server
    socketio.run(app, host='127.0.0.1', port='5000', debug=True, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()

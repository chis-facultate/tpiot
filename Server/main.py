from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import csv

# Global variables
app = Flask(__name__)  # Flask app instance
socketio = SocketIO(app)
stations_data = []
item_data_dict = {}


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
    print("Station data loaded successfully.")
    print(stations_data)


def load_item_data(file_path):
    global item_data_dict
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item_name = row['Item name']
            item_data_dict[item_name] = {  # Item code is useless
                'Unit of measurement': row['Unit of measurement'],
                'Good': float(row['Good(Blue)']),
                'Normal': float(row['Normal(Green)']),
                'Bad': float(row['Bad(Yellow)']),
                'Very bad': float(row['Very bad(Red)'])
            }
    print("Item data loaded successfully.")
    print(item_data_dict)


# Endpoints
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/stations', methods=['GET'])
def get_stations():
    return jsonify(stations_data)


# Receive data from the POST request and forward it to WebSocket clients
@app.route('/data', methods=['POST'])
def receive_data():
    try:
        # Get JSON data from the POST request (from the gateway)
        json_data = request.get_json()

        # Check that json_data is a valid dictionary
        if not isinstance(json_data, dict):
            raise ValueError("Invalid data format")

        # Log the received data for debugging
        print(f"Received data: {json_data}")

        # Send the received data to the client using WebSocket
        socketio.emit('update_station_data', json_data)

        # Return a successful response to the gateway
        return jsonify({'status': 'success', 'message': 'Data received and forwarded to client'}), 200
    except Exception as e:
        print(f"Error receiving or forwarding data: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to receive data'}), 500


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
    stations_data_file_path = './data/Measurement_station_info.csv'
    items_data_file_path = './data/Measurement_item_info.csv'
    load_stations_data(stations_data_file_path)
    load_item_data(items_data_file_path)
    # Run Flask server
    # app.run(debug=True)
    socketio.run(app, host='127.0.0.1', port='5000', debug=True, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()

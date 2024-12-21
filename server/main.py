import eventlet
eventlet.monkey_patch()  # This must be called before any other imports

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from pymongo import MongoClient
import logging
import copy

# Global variables
app = Flask(__name__)
socketio = SocketIO(app)
last_read_values = {}

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Capture all log levels
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# MongoDB Configuration
mongo_client = MongoClient("mongodb+srv://user1:asdfsdfdzc13reqfvdf@cluster0.cve6w.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client['tpiot_db']

# AQI thresholds
minimum_aqi = 0
good_aqi_high = 50
normal_aqi_high = 100
bad_aqi_high = 250
maximum_aqi = 500

# Data
stations_data = [
  {
    "Station code": 101,
    "Station name": "Jongno-gu",
    "Address": "19, Jong-ro 35ga-gil, Jongno-gu, Seoul, Republic of Korea",
    "Latitude": 37.572016399999995,
    "Longitude": 127.00500749999999
  },
  {
    "Station code": 102,
    "Station name": "Jung-gu",
    "Address": "15, Deoksugung-gil, Jung-gu, Seoul, Republic of Korea",
    "Latitude": 37.564262899999996,
    "Longitude": 126.97467569999999
  },
  {
    "Station code": 103,
    "Station name": "Yongsan-gu",
    "Address": "136, Hannam-daero, Yongsan-gu, Seoul, Republic of Korea",
    "Latitude": 37.540032700000005,
    "Longitude": 127.00485
  },
  {
    "Station code": 104,
    "Station name": "Eunpyeong-gu",
    "Address": "215, Jinheung-ro, Eunpyeong-gu, Seoul, Republic of Korea",
    "Latitude": 37.6098232,
    "Longitude": 126.9348476
  },
  {
    "Station code": 105,
    "Station name": "Seodaemun-gu",
    "Address": "32, Segeomjeong-ro 4-gil, Seodaemun-gu, Seoul, Republic of Korea",
    "Latitude": 37.5937421,
    "Longitude": 126.9496787
  },
  {
    "Station code": 106,
    "Station name": "Mapo-gu",
    "Address": "10, Poeun-ro 6-gil, Mapo-gu, Seoul, Republic of Korea",
    "Latitude": 37.555580299999995,
    "Longitude": 126.90559750000001
  },
  {
    "Station code": 107,
    "Station name": "Seongdong-gu",
    "Address": "18, Ttukseom-ro 3-gil, Seongdong-gu, Seoul, Republic of Korea",
    "Latitude": 37.541864200000006,
    "Longitude": 127.04965890000001
  },
  {
    "Station code": 108,
    "Station name": "Gwangjin-gu",
    "Address": "571, Gwangnaru-ro, Gwangjin-gu, Seoul, Republic of Korea",
    "Latitude": 37.547180299999994,
    "Longitude": 127.0924929
  },
  {
    "Station code": 109,
    "Station name": "Dongdaemun-gu",
    "Address": "43, Cheonho-daero 13-gil, Dongdaemun-gu, Seoul, Republic of Korea",
    "Latitude": 37.57574279999999,
    "Longitude": 127.0288848
  },
  {
    "Station code": 110,
    "Station name": "Jungnang-gu",
    "Address": "369, Yongmasan-ro, Jungnang-gu, Seoul, Republic of Korea",
    "Latitude": 37.5848485,
    "Longitude": 127.0940229
  },
  {
    "Station code": 111,
    "Station name": "Seongbuk-gu",
    "Address": "70, Samyang-ro 2-gil, Seongbuk-gu, Seoul, Republic of Korea",
    "Latitude": 37.606718900000004,
    "Longitude": 127.0272794
  },
  {
    "Station code": 112,
    "Station name": "Gangbuk-gu",
    "Address": "49, Samyang-ro 139-gil, Gangbuk-gu, Seoul, Republic of Korea",
    "Latitude": 37.6479299,
    "Longitude": 127.01195179999999
  },
  {
    "Station code": 113,
    "Station name": "Dobong-gu",
    "Address": "34, Sirubong-ro 2-gil, Dobong-gu, Seoul, Republic of Korea",
    "Latitude": 37.6541919,
    "Longitude": 127.0290879
  },
  {
    "Station code": 114,
    "Station name": "Nowon-gu",
    "Address": "17, Sanggye-ro 23-gil, Nowon-gu, Seoul, Republic of Korea",
    "Latitude": 37.6587743,
    "Longitude": 127.0685054
  },
  {
    "Station code": 115,
    "Station name": "Yangcheon-gu",
    "Address": "56, Jungang-ro 52-gil, Yangcheon-gu, Seoul, Republic of Korea",
    "Latitude": 37.5259388,
    "Longitude": 126.85660290000001
  },
  {
    "Station code": 116,
    "Station name": "Gangseo-gu",
    "Address": "71, Gangseo-ro 45da-gil, Gangseo-gu, Seoul, Republic of Korea",
    "Latitude": 37.54464,
    "Longitude": 126.8351506
  },
  {
    "Station code": 117,
    "Station name": "Guro-gu",
    "Address": "45, Gamasan-ro 27-gil, Guro-gu, Seoul, Republic of Korea",
    "Latitude": 37.498498100000006,
    "Longitude": 126.88969240000002
  },
  {
    "Station code": 118,
    "Station name": "Geumcheon-gu",
    "Address": "20, Geumha-ro 21-gil, Geumcheon-gu, Seoul, Republic of Korea",
    "Latitude": 37.4523569,
    "Longitude": 126.9082956
  },
  {
    "Station code": 119,
    "Station name": "Yeongdeungpo-gu",
    "Address": "11, Yangsan-ro 23-gil, Yeongdeungpo-gu, Seoul, Republic of Korea",
    "Latitude": 37.5250065,
    "Longitude": 126.89737050000001
  },
  {
    "Station code": 120,
    "Station name": "Dongjak-gu",
    "Address": "6, Sadang-ro 16a-gil, Dongjak-gu, Seoul, Republic of Korea",
    "Latitude": 37.4809167,
    "Longitude": 126.9714807
  },
  {
    "Station code": 121,
    "Station name": "Gwanak-gu",
    "Address": "14, Sillimdong-gil, Gwanak-gu, Seoul, Republic of Korea",
    "Latitude": 37.4873546,
    "Longitude": 126.927102
  },
  {
    "Station code": 122,
    "Station name": "Seocho-gu",
    "Address": "16, Sinbanpo-ro 15-gil, Seocho-gu, Seoul, Republic of Korea",
    "Latitude": 37.5045471,
    "Longitude": 126.99445779999999
  },
  {
    "Station code": 123,
    "Station name": "Gangnam-gu",
    "Address": "426, Hakdong-ro, Gangnam-gu, Seoul, Republic of Korea",
    "Latitude": 37.5175282,
    "Longitude": 127.0474699
  },
  {
    "Station code": 124,
    "Station name": "Songpa-gu",
    "Address": "236, Baekjegobun-ro, Songpa-gu, Seoul, Republic of Korea",
    "Latitude": 37.5026857,
    "Longitude": 127.0925092
  },
  {
    "Station code": 125,
    "Station name": "Gangdong-gu",
    "Address": "59, Gucheonmyeon-ro 42-gil, Gangdong-gu, Seoul, Republic of Korea",
    "Latitude": 37.5449625,
    "Longitude": 127.13679170000002
  }
]

items_data_dict = {
    'SO2': {'Good': 0.02, 'Normal': 0.05, 'Bad': 0.15, 'Very bad': 1.0},
    'NO2': {'Good': 0.03, 'Normal': 0.06, 'Bad': 0.2, 'Very bad': 2.0},
    'CO': {'Good': 2.0, 'Normal': 9.0, 'Bad': 15.0, 'Very bad': 50.0},
    'O3': {'Good': 0.03, 'Normal': 0.09, 'Bad': 0.15, 'Very bad': 0.5},
    'PM10': {'Good': 30.0, 'Normal': 80.0, 'Bad': 150.0, 'Very bad': 500.0},
    'PM2.5': {'Good': 15.0, 'Normal': 35.0, 'Bad': 75.0, 'Very bad': 500.0}
}


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
        logger.debug('Concentration exceeds tha maximum concentration')
        exit(1)

    # Apply the linear interpolation formula to calculate the AQI
    aqi = (((concentration - concentration_low) * (index_high - index_low)) / (concentration_high - concentration_low)
           + index_low)

    if aqi > maximum_aqi:
        logger.debug('AQI exceeds maximum AQI possible')
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


def calculate_aqi_for_all_items(station_data_dict):
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


# Page endpoints
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/history', methods=['GET'])
def history():
    station_code = request.args.get('stationCode', default='', type=str)
    return render_template('history.html', stationCode=station_code)


# Data endpoints
@app.route('/stations', methods=['GET'])
def get_stations():
    return jsonify(stations_data)


@app.route('/last_read_values', methods=['GET'])
def get_last_read_values():
    return jsonify(last_read_values)


@app.route('/history_data/<station_code>', methods=['GET'])
def get_history_data(station_code):
    collection = db[station_code]
    documents = list(collection.find({}, {'_id': 0}))  # Exclude the MongoDB _id field
    return jsonify(documents)


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
        logger.debug(f'Error receiving data: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to receive data'}), 500

    # Log the received data
    logger.debug(f'Received data: {data_dict}')

    # Calculate AQI
    aqi_dict = calculate_aqi_for_all_items(data_dict)

    # Update last read values dictionary
    station_code = aqi_dict['Station code']
    global last_read_values
    last_read_values[station_code] = aqi_dict['Sensors data']

    # Send the processed data to the client using WebSocket
    try:
        socketio.emit('update_station_data', aqi_dict)
        logger.debug(f'Data forwarded on update_station_data: {aqi_dict}')
        socketio.emit('update_station_' + station_code + '_history', last_read_values[station_code])
        logger.debug(f'Data forwarded on update_station_stationCode_history: {last_read_values[station_code]}')
    except Exception as e:
        logger.debug(f'Error forwarding data: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to forward data'}), 500

    # Save the new data in databse
    try:
        collection = db[station_code]
        collection.insert_one(last_read_values[station_code])
    except Exception as e:
        logger.debug(f'Error saving data in db: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to save data in db'}), 500

    # Return a successful response to the gateway
    return jsonify({'status': 'success', 'message': 'Data received and forwarded to client'}), 200


# SocketIO event for client connection
@socketio.on('connect')
def handle_connect():
    client_ip = request.remote_addr
    client_port = request.environ.get('REMOTE_PORT')
    logger.debug(f'Client connected from {client_ip}:{client_port}')


# SocketIO event for client disconnection
@socketio.on('disconnect')
def handle_disconnect():
    client_ip = request.remote_addr
    client_port = request.environ.get('REMOTE_PORT')
    logger.debug(f'Client disconnected from {client_ip}:{client_port}')


def main():
    # Run Flask server
    socketio.run(app, host='0.0.0.0', port='5000', debug=True, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()

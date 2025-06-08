import subprocess
import sys
import logging

# Configure logging for your main script
logging.basicConfig(filename='station_item_log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

station_start = 101
station_end = 125
item_codes = [1, 3, 5, 6, 8, 9]
program = r"C:\Users\this-user\Documents\GitHub\tpiot\device\main.py"  # Raw string path

# Launch all processes
processes = []

for station in range(station_start, station_end + 1):
    station_code = str(station)
    for item in item_codes:
        item_code = str(item)
        # Run subprocess with real-time output to console
        proc = subprocess.Popen(
            ['python', program, station_code, item_code],
            stdout=sys.stdout,  # Direct output to console
            stderr=sys.stderr   # Direct errors to console
        )
        processes.append((station_code, item_code, proc))

# Wait for all processes to complete
for station_code, item_code, proc in processes:
    proc.wait()
    logging.info(f'Process for station {station_code} and item {item_code} completed')

import subprocess
import datetime
import sys

program = r'C:\Users\this-user\Documents\GitHub\tpiot\gateway\main.py'  # Raw string for Windows path
processes = []

for i in range(101, 102):
    print(f"{datetime.datetime.now()}: Starting run with argument {i}")
    # Start subprocess without waiting
    proc = subprocess.Popen(['python', program, str(i)],
                            stdout=sys.stdout,
                            stderr=sys.stderr,
                           )
    processes.append((str(i), proc))

# Wait for all processes to complete and collect output
for i, proc in processes:
    proc.wait()
    logging.info(f'Process for gateway {i} completed')

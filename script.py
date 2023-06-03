import sys
import time
import schedule
from app import job

if len(sys.argv) < 2:
    print("Error: Please provide the ICAO24 value as a command-line argument.")
    sys.exit(1)
icao24 = sys.argv[1]
schedule.every(2).minutes.do(job, icao24, 'OPENSKYUSERNAME', 'OPENSKYPASSWORD', 'db.sqlite3')
while True:
    schedule.run_pending()
    time.sleep(1)

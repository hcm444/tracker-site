import datetime
import sys
import requests
from flask_caching import Cache
from flask import make_response, after_this_request
from map import map
from flask import Flask, render_template

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, app=app)
import sqlite3
import time
from flask_caching import Cache
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
if len(sys.argv) < 2:
    print("Error: Please provide the ICAO24 value as a command-line argument.")
    sys.exit(1)
global ICAO24
ICAO24 = sys.argv[1]


def get_latest_data(database):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("""
        SELECT f1.* FROM aircraft_states f1
        LEFT JOIN aircraft_states f2
        ON f1.icao24 = f2.icao24 AND f1.timestamp < f2.timestamp
        WHERE f2.timestamp IS NULL AND f1.timestamp = (
            SELECT MAX(timestamp) FROM aircraft_states
        )
    """)
    latest_data = c.fetchall()
    conn.close()
    return latest_data


def create_table(database):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS aircraft_states (
                    icao24 TEXT,
                    callsign TEXT,
                    origin_country TEXT,
                    time_position INTEGER,
                    last_contact INTEGER,
                    longitude REAL,
                    latitude REAL,
                    baro_altitude REAL,
                    on_ground INTEGER,
                    velocity REAL,
                    true_track REAL,
                    vertical_rate REAL,
                    sensors TEXT,
                    geo_altitude REAL,
                    squawk TEXT,
                    spi INTEGER,
                    position_source INTEGER,
                    timestamp INTEGER
                )''')
    conn.commit()
    conn.close()


def insert_state(state, database):
    if state and state['states']:
        conn = sqlite3.connect(database)
        c = conn.cursor()
        for aircraft_state in state['states']:
            timestamp = int(time.time())
            aircraft_state.append(timestamp)
            c.execute('''
                INSERT INTO aircraft_states 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', aircraft_state)
        conn.commit()
        conn.close()
    else:
        print("Error: Missing aircraft state data.")


def get_aircraft_info(icao24, username, password):
    url = f"https://opensky-network.org/api/states/all?icao24={icao24}"
    response = requests.get(url, auth=(username, password))
    if response.status_code == 200:
        data = response.json()
        print("Successfully pulled Opensky Data")
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def job(icao24, username, password, database):
    print("Pulling new OpenSky data...")
    aircraft_info = get_aircraft_info(icao24, username, password)
    print(aircraft_info)
    if aircraft_info and aircraft_info['states']:
        create_table(database)
        insert_state(aircraft_info, database)
    else:
        print("Error: Missing Opensky state data.")


@app.route('/')
@limiter.limit("20 per minute")
@cache.cached(timeout=60)  # Cache the result of this route for 60 seconds
def map_image():
    label = ICAO24
    latest_data = get_latest_data('db.sqlite3')
    if len(latest_data) == 0:
        latest_time = "No data available"
    else:
        latest_time = datetime.datetime.utcfromtimestamp(latest_data[0][17])
    map_image_data0 = map(12, 'db.sqlite3', label)
    map_image_data1 = map(9, 'db.sqlite3', label)
    map_image_data2 = map(6, 'db.sqlite3', label)
    map_image_data3 = map(3, 'db.sqlite3', label)
    rendered_template = render_template('index.html', image_data0=map_image_data0,
                                        image_data1=map_image_data1,
                                        image_data2=map_image_data2,
                                        image_data3=map_image_data3,
                                        latest_data=latest_data,
                                        latest_time=latest_time)
    cache.set('map_image_data', rendered_template)
    response = make_response(rendered_template)

    @after_this_request
    def update_cache(response):
        cache.set('map_image_data', response.get_data(as_text=True))
        return response

    return response


if __name__ == '__main__':
    app.run(debug=False)

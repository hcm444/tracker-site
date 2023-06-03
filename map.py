import base64
import io
import sqlite3
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


def map(map_padding, database, icao24):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT longitude, latitude FROM aircraft_states ORDER BY time_position DESC LIMIT 180')
    states1 = c.fetchall()
    conn.close()
    states = states1[::-1]
    longitudes = [state[0] for state in states if state[0] is not None]
    latitudes = [state[1] for state in states if state[1] is not None]
    if len(longitudes) == 0 or len(latitudes) == 0:
        return None
    center_lon = sum(longitudes) / len(longitudes)
    center_lat = sum(latitudes) / len(latitudes)
    most_recent_state = states[-1]
    most_recent_lon = most_recent_state[0]
    most_recent_lat = most_recent_state[1]
    min_lon = most_recent_lon - map_padding
    max_lon = most_recent_lon + map_padding
    min_lat = most_recent_lat - map_padding
    max_lat = most_recent_lat + map_padding
    fig = plt.figure(figsize=(10, 10), facecolor='green')
    m = Basemap(projection='cyl', resolution='l',
                llcrnrlon=min_lon, llcrnrlat=min_lat,
                urcrnrlon=max_lon, urcrnrlat=max_lat)
    m.drawcoastlines()
    m.drawcountries()
    m.drawcounties()
    m.drawstates()
    m.drawmapboundary(fill_color='black')
    m.fillcontinents(color='green', lake_color='black')
    m.drawparallels(range(int(min_lat), int(max_lat) + 1, 2), labels=[1, 0, 0, 0], color='green')
    m.drawmeridians(range(int(min_lon), int(max_lon) + 1, 2), labels=[0, 0, 0, 1], color='green')
    fade_colors = [(1, 0, 0, i / len(states)) for i in range(len(states))]
    m.plot(longitudes, latitudes, color='white', linewidth=2, alpha=0.5)
    m.scatter(longitudes[-1], latitudes[-1], color='white', marker='o')
    annotation_text = icao24
    annotation_x, annotation_y = m(most_recent_lon, most_recent_lat)
    plt.annotate(annotation_text, xy=(annotation_x, annotation_y),
                 xytext=(annotation_x + 0.5, annotation_y + 0.5),
                 color='white', fontsize=10)
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    return image_data

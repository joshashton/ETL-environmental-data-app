#imports
import requests
from pprint import pprint
import pandas as pd
import numpy as np 

import os
import warnings
# Suppress FutureWarning messages
warnings.simplefilter(action='ignore', category=FutureWarning)

import difflib 

#database connection
import psycopg2 as psql 
from dotenv import load_dotenv
import os
import base64
import pprint

from statistics import mean
from datetime import datetime, timedelta

#secrets
load_dotenv()

username = os.getenv('sql_user')
password = os.getenv('sql_pass')
host = os.getenv('host')

api_key = os.getenv('API_KEY')
NASA_api_key = os.getenv('NASA_API_KEY')
METEOSTAT_api_key = os.getenv('METEOSTAT_API_KEY')

conn = psql.connect(database = 'pagila', 
                    user = username, 
                    host = host, 
                    password = password, 
                    port = 5432)
cur = conn.cursor()

#dates
cur.execute("""
    SELECT 
        (SELECT MAX(date) FROM student.de10_ja_weather) AS max_weather_date,
        (SELECT MAX(time) FROM student.de10_ja_earthquake) AS max_earthquake_time,
        (SELECT MAX(time) FROM student.de10_ja_natural_disasters) AS max_natural_disasters_time,
        (SELECT MAX(date) FROM student.de10_ja_neo) AS max_neo_date,
        (SELECT MAX(date) FROM student.de10_ja_apod) AS max_apod_date
""")

# Fetch the result - last data inserted into db
value = cur.fetchone()

# Convert to datetime objects
max_weather_date = datetime.strptime(value[0], '%Y-%m-%d')
max_earthquake_date = datetime.strptime(value[1][:10], '%Y-%m-%d')
max_disaster_date = datetime.strptime(value[2][:10], '%Y-%m-%d')
max_neo_date = value[3]
max_apod_date = value[4]
# Add one day to each date
weather_start_date = datetime.strftime(max_weather_date + timedelta(days=1), '%Y-%m-%d')
earthquake_start_date = datetime.strftime(max_earthquake_date + timedelta(days=1), '%Y-%m-%d')
disaster_start_date = datetime.strftime(max_disaster_date + timedelta(days=1), '%Y-%m-%d')
neo_start_date = datetime.strftime(max_neo_date + timedelta(days=1), '%Y-%m-%d')
apod_start_date = datetime.strftime(max_apod_date + timedelta(days=1), '%Y-%m-%d')

today = datetime.today().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

#function to make api call
def get_API_JSON(url):
    try:
        response = requests.get(url)
        JSONRes = response.json()
        return JSONRes
    except:
        return None


#weather
#get previous days weather in the morning
#get every countries lat and lon to update weather for
countries_df = pd.read_csv('Data/capital_locations.csv')
latitudes = countries_df['latitude'].unique()
longitudes = countries_df['longitude'].unique()

# Convert float values to strings and join them with commas
lat_string = ",".join(map(str, latitudes))
long_string = ",".join(map(str, longitudes))

weather_url = f'https://api.open-meteo.com/v1/forecast?latitude={lat_string}&longitude={long_string}&start_date={weather_start_date}&end_date={yesterday}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max'

#dont get data thats already in db
if max_weather_date.strftime('%Y-%m-%d') == yesterday:
    weather_response = None
else:    
    weather_response = get_API_JSON(weather_url)

if weather_response:
    weather_rows = []
    #loop through JSON
    id_count = 1
    for location in weather_response:
        country_id = id_count
        loop_count = 0
    
        # Loop through each day's data
        for i, time in enumerate(location['daily']['time']):
           
            date = time
            max_temp = location['daily']['temperature_2m_max'][i]
            min_temp = location['daily']['temperature_2m_min'][i]
            precipitation = location['daily']['precipitation_sum'][i]
            wind_speed = location['daily']['wind_speed_10m_max'][i]
            
            if max_temp is not None and min_temp is not None:
                avg_temp = mean([max_temp, min_temp])          
            else:
                avg_temp = None
            
            weather_rows.append({
                'date': date,
                'avg_temp_c': avg_temp,
                'precipitation_mm' : precipitation,
                'avg_wind_speed_kmh' : wind_speed,
                'country_id' : country_id
            })
        id_count +=1
    
    weather_data = pd.DataFrame(weather_rows)
    for row in weather_data.iterrows():
        sql = f"""
        INSERT INTO student.de10_ja_weather(date, avg_temp_c, precipitation_mm, avg_wind_speed_kmh, country_id)
        VALUES ('{row[1][0]}',
        {row[1][1]},
        {row[1][2]},
        {row[1][3]},
        {row[1][4]})
        """ 
        # Execute the SQL command
        cur.execute(sql)

##earthquake
#get previous days earthquakes in morning
earthquake_url = f'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={earthquake_start_date}&endtime={yesterday}&minmagnitude=5'

#dont get data thats already in db
if max_earthquake_date.strftime('%Y-%m-%d') == yesterday:
    earthquake_response = None
else:    
    earthquake_response = get_API_JSON(earthquake_url)

#collect data
if earthquake_response and earthquake_response['features']:
    earthquake_list = []
    for earthquake in earthquake_response['features']:
        data = {
            'time': earthquake['properties']['time'],
            'latitude': earthquake['geometry']['coordinates'][1],
            'longitude': earthquake['geometry']['coordinates'][0],
            'mag': earthquake['properties']['mag'],
            'magType': earthquake['properties']['magType'],
            'place': earthquake['properties']['place']
            }  
        earthquake_list.append(data)

    earthquake_data = pd.DataFrame(earthquake_list)
    earthquake_data['time'] = pd.to_datetime(earthquake_data['time'], unit='ms',origin='unix', utc=True) 
    #flip df
    earthquake_data[:] = earthquake_data[::-1]
    for _, row in earthquake_data.iterrows():
        
        sql = """
            INSERT INTO student.de10_ja_earthquake(time, latitude, longitude, mag, magType, place)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
        # Execute the SQL command
        cur.execute(sql, (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5]
        ))


#natural disasters
#get previous days natural disasters in morning
days = datetime.now() - max_disaster_date
disaster_url = f'https://eonet.gsfc.nasa.gov/api/v2.1/events?days={days.days}'

#dont get data thats already in db
if max_disaster_date.strftime('%Y-%m-%d') == yesterday:
    disaster_response = None
else:    
    disaster_response = get_API_JSON(disaster_url)

#collect data
if disaster_response and disaster_response['events']:
    disaster_list = []
    for x in disaster_response["events"]:
        name = x['title']
        type = x['categories'][-1]['title'] #-1 to get latest location of event
        lat = x['geometries'][-1]['coordinates'][1]
        lon = x['geometries'][-1]['coordinates'][0]
        date = x['geometries'][-1]['date']
        
        disaster_list.append({
            'time': date,
            'latitude': lat,
            'longitude': lon,
            'name': name,
            'type': type     
        })

    disasters_data = pd.DataFrame(disaster_list)
    for _, row in disasters_data.iterrows():
        
        sql = """
            INSERT INTO student.de10_ja_natural_disasters(time, latitude, longitude, name, type)
            VALUES (%s, %s, %s, %s, %s)
            """
        # Execute the SQL command
        cur.execute(sql, (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            ))


#apod
apod_url = f'https://api.nasa.gov/planetary/apod?api_key={NASA_api_key}&start_date={apod_start_date}&end_date={today}'

#dont get data thats already in db
if max_apod_date.strftime('%Y-%m-%d') == today:
    apod_response = None
else:    
    apod_response = get_API_JSON(apod_url)

#collect data
if apod_response:
    apod_list = []
    for x in apod_response:
        name = x['title']
        explanation = x['explanation']
        date = x['date']
        image = x['url']
        
        apod_list.append({
            'name': name,
            'explanation': explanation,
            'date': date,
            'image': image 
        })

    apod_data = pd.DataFrame(apod_list)
    for _, row in apod_data.iterrows():
        
        sql = """
            INSERT INTO student.de10_ja_apod(name, explanation, date, image)
            VALUES (%s, %s, %s, %s)
            """
        # Execute the SQL command
        cur.execute(sql, (
            row[0],
            row[1],
            row[2],
            row[3],
            ))

#neos
#get todays neos in the morning
neo_url = f'https://api.nasa.gov/neo/rest/v1/feed?start_date={neo_start_date}&end_date={today}&api_key={NASA_api_key}'

#dont get data thats already in db
if max_neo_date.strftime('%Y-%m-%d') == today:
    neo_response = None
else:    
    neo_response = get_API_JSON(neo_url)

#collect data
if neo_response:
    neo_list = []
    for x in neo_response["near_earth_objects"]:
        for y in neo_response["near_earth_objects"][x]:
            date = x
            name = y['name']
            neo_id = y['neo_reference_id']
            miss_miles = y['close_approach_data'][0]['miss_distance']['miles']
            diameter_miles = y['estimated_diameter']['miles']['estimated_diameter_max']
            is_hazardous = y['is_potentially_hazardous_asteroid'] 
        
            neo_list.append({
                'neo_id': neo_id,
                'name' : name,
                'date': date,
                'miss_miles': miss_miles,
                'diameter_miles': diameter_miles,
                'is_hazardous': is_hazardous     
            })
    
    neo_data = pd.DataFrame(neo_list)
    #flip
    neo_data[:] = neo_data[::-1]
    #SQL
    for _, row in neo_data.iterrows():
        
        sql = """
            INSERT INTO student.de10_ja_neo(neo_id, name, date, miss_miles, diameter_miles, is_hazardous)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
        # Execute the SQL command
        cur.execute(sql, (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            ))

carbon_url = f'https://api.carbonintensity.org.uk/regional'
carbon_response = get_API_JSON(carbon_url)
#collect data
if carbon_response:
    carbon_list = []
    
    for region in carbon_response['data'][0]['regions']:
        
        data = {
            'from': carbon_response['data'][0]['from'],
            'to': carbon_response['data'][0]['to'],
            
            'regionid': region['regionid'],
            'dnoregion': region['dnoregion'],
            'shortname': region['shortname'],
            'forecast': region['intensity']['forecast'],
            'index': region['intensity']['index'],
            
            'biomass': region['generationmix'][0]['perc'],
            'coal': region['generationmix'][1]['perc'],
            'imports': region['generationmix'][2]['perc'],
            'gas': region['generationmix'][3]['perc'],
            'nuclear': region['generationmix'][4]['perc'],
            'other': region['generationmix'][5]['perc'],
            'hydro': region['generationmix'][6]['perc'],
            'solar': region['generationmix'][7]['perc'],
            'wind': region['generationmix'][8]['perc']
           # 'index': region['intensity']['index']
        }
        carbon_list.append(data)

    carbon_data = pd.DataFrame(carbon_list)
    
    for _, row in carbon_data.iterrows():
    
        sql = """
            INSERT INTO student.de10_ja_carbon("from", "to", regionid, dnoregion, shortname, forecast,"index",biomass,coal,imports,gas,nuclear,other,hydro,solar,wind)
            VALUES (%s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s)
            """
        # Execute the SQL command
        cur.execute(sql, (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            row[9],
            row[10],
            row[11],
            row[12],
            row[13],
            row[14],
            row[15],
            ))


conn.commit()
conn.close()

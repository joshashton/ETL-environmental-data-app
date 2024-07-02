import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt # visualisation!
import plotly.express as px
import plotly.graph_objects as go

#database connection
import psycopg2 as psql 

## Requests is the default library for asking python to talk to the web
import requests
## PPrint is 'Pretty Print' Which lets us print less offensive JSON
from pprint import pprint
from datetime import datetime, timedelta


#get dates
today_date = datetime.today().strftime('%Y-%m-%d')

def get_ttl():
    # Calculate the ttl until 3 AM the next day for CRON job
    now = datetime.now()
    next_day = now + timedelta(days=1)
    next_3am = next_day.replace(hour=3, minute=0, second=0, microsecond=0)
    ttl = next_3am - now
    return ttl

#DB connection
# Initialize connection.
conn = st.connection("postgresql",type="sql")
# Get latest dates from DB for all data sources
query = '''
    SELECT 
        (SELECT MAX(date) FROM student.de10_ja_weather) AS max_weather_date,
        (SELECT MAX(time) FROM student.de10_ja_earthquake) AS max_earthquake_time,
        (SELECT MAX(time) FROM student.de10_ja_natural_disasters) AS max_natural_disasters_time,
        (SELECT MAX(date) FROM student.de10_ja_neo) AS max_neo_date,
        (SELECT MAX(date) FROM student.de10_ja_apod) AS max_apod_date
'''
dates = conn.query(query, ttl=get_ttl())

# Convert to datetime objects
max_weather_date = datetime.strptime(dates['max_weather_date'][0], '%Y-%m-%d').strftime('%Y-%m-%d')
max_earthquake_date = datetime.strptime(dates['max_earthquake_time'][0][:10], '%Y-%m-%d').strftime('%Y-%m-%d')
max_disaster_date = datetime.strptime(dates['max_natural_disasters_time'][0][:10], '%Y-%m-%d').strftime('%Y-%m-%d')
max_neo_date = dates['max_neo_date'][0].strftime('%Y-%m-%d')
max_apod_date = dates['max_apod_date'][0].strftime('%Y-%m-%d')

# Read the CSV file into a DataFrame
countries_df = pd.read_csv('DataSetup/Data/capital_locations.csv')

st.title("Environmental Information Hub")

tab1, tab2 = st.tabs(["🌍 Earth", "🚀 Space"])

#Earth section
with tab1:
    st.header("Climate Stats")


    st.subheader("Weather")
    city = st.text_input("Enter city name:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if city:
            st.metric("Temperature", "70 °F", "1.2 °F")
    with col2:
        if city:
            st.metric("Wind", "9 mph", "-8%")        
    with col3:
        if city:
            st.metric("Humidity", "86%", "4%")

    # Forecast of chosen weather

    # weather - this time last year
    # Analyse a Handfull of major cites 

    st.subheader("Historical Weather Analysis ")

    weather_options = st.multiselect(
        "Countries to analyse:", 
        countries_df['country'],
        ['United Kingdom'])

    if weather_options:
        st.metric("Temperature", "26 C", "4 C from last year")



#Space section
with tab2:
    st.header("Space Stats")
    query = f"SELECT * FROM student.de10_ja_apod ORDER BY date DESC LIMIT 1;"
    apod_data = conn.query(query, ttl=get_ttl())
    st.write(apod_data)
    name, explanation, date, url = apod_data.iloc[0]
    st.subheader(f"Astronomy Picture of the Day (APOD)")
    st.image(url, caption=f'{name} ({date})', use_column_width=True)
    st.write(explanation)

    st.subheader(f"Near Earth Objects (NEO)")
    query = f"SELECT * FROM student.de10_ja_neo where DATE(date) = '{max_neo_date}';"
    neo_data = conn.query(query, ttl=get_ttl())
    st.write(neo_data)


    #NEO Plot
     # Define a function to adjust marker size based on diameter
    def adjust_marker_size(diameter):
        if diameter > 0.099:
            return diameter * 50  # Adjust multiplier for larger diameters
        else:
            return diameter * 200  # Adjust multiplier for smaller diameters
    # Earth position
    earth_x, earth_y, earth_z = 0, 0, 0

    # Create random angles for the asteroid positions around Earth
    theta = np.linspace(0, 2 * np.pi, len(neo_data['miss_miles']))
    phi = np.linspace(0, np.pi, len(neo_data['miss_miles']))

    # Calculate the positions of the asteroids in 3D space
    xs = np.array(neo_data['miss_miles']) * np.cos(theta) * np.sin(phi)
    ys = np.array(neo_data['miss_miles']) * np.sin(theta) * np.sin(phi)
    zs = np.array(neo_data['miss_miles']) * np.cos(phi)

    # Create a DataFrame
    neo_3d_df = pd.DataFrame({
        'x': xs,
        'y': ys,
        'z': zs,
        'diameter': neo_data['diameter_miles'],
        'miss_miles': neo_data['miss_miles'],
        'is_hazardous': neo_data['is_hazardous'],
        'neo_id': neo_data['neo_id'],  # Assuming you have a column named 'neo_id'
        'name': neo_data['name']  # Assuming you have a column named 'name'
    })

    # Create the 3D scatter plot
    fig = go.Figure()   

    # Plot Earth in the center
    fig.add_trace(go.Scatter3d(
        x=[earth_x],
        y=[earth_y],
        z=[earth_z],
        mode='markers',
        marker=dict(size=10, color='blue'),  # Adjust size for visibility
        hoverinfo='text',
        text='Planet: Earth<br>Diameter: 7917.5 miles',
        name='Earth',
        showlegend=True  # Ensure Earth shows in the legend
    ))

    # Plot non-hazardous asteroids around Earth
    fig.add_trace(go.Scatter3d(
        x=neo_3d_df[neo_3d_df['is_hazardous'] == False]['x'],  # Filter for non-hazardous asteroids
        y=neo_3d_df[neo_3d_df['is_hazardous'] == False]['y'],
        z=neo_3d_df[neo_3d_df['is_hazardous'] == False]['z'],
        mode='markers',
        marker=dict(
            size=neo_3d_df['diameter'].apply(adjust_marker_size),  # Scale diameter for visibility
            color='green',  # Color for non-hazardous asteroids
            opacity=0.7
        ),
        name='Non-Hazardous Asteroids',
        hoverinfo='text',
        text=neo_3d_df.apply(lambda row:
                            f"Name: {row['name']}<br>"
                            f"NEO ID: {row['neo_id']}<br>"
                            f"Miss Distance: {row['miss_miles']} miles<br>"
                            f"Diameter: {row['diameter']} miles",
                            axis=1),
        showlegend=True  # Ensure non-hazardous asteroids show in the legend
    ))

    # Plot hazardous asteroids around Earth
    fig.add_trace(go.Scatter3d(
        x=neo_3d_df[neo_3d_df['is_hazardous'] == True]['x'],  # Filter for hazardous asteroids
        y=neo_3d_df[neo_3d_df['is_hazardous'] == True]['y'],
        z=neo_3d_df[neo_3d_df['is_hazardous'] == True]['z'],
        mode='markers',
        marker=dict(
            size=neo_3d_df['diameter'].apply(adjust_marker_size),  # Scale diameter for visibility
            color='red',  # Color for hazardous asteroids
            opacity=0.7
        ),
        name='Hazardous Asteroids',
        hoverinfo='text',
        text=neo_3d_df.apply(lambda row:
                            f"Name: {row['name']}<br>"
                            f"NEO ID: {row['neo_id']}<br>"
                            f"Miss Distance: {row['miss_miles']} miles<br>"
                            f"Diameter: {row['diameter']} miles",
                            axis=1),
        showlegend=True  # Ensure hazardous asteroids show in the legend
    ))

    # Set axis limits based on the maximum distance
    max_distance = 1.2 * max(neo_data['miss_miles'])
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-max_distance, max_distance]),
            yaxis=dict(range=[-max_distance, max_distance]),
            zaxis=dict(range=[-max_distance, max_distance])
        ),
        title=f"3D Plot of Asteroids around Earth on {max_neo_date}",
        scene_aspectmode='cube', # Ensure the aspect ratio is equal
    )

    # Display the plot
    #fig.show()
    fig.update_layout(autosize= True, height = 600, margin = dict(t = 50, b =100), legend = dict(itemsizing = "constant"))
    st.plotly_chart(fig, theme="streamlit")


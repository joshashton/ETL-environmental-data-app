import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt # visualisation!
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

#database connection
import psycopg2 as psql 

## Requests is the default library for asking python to talk to the web
import requests
## PPrint is 'Pretty Print' Which lets us print less offensive JSON
from pprint import pprint
from datetime import datetime, timedelta, date


#get dates
today_date = datetime.today().strftime('%Y-%m-%d')

def get_ttl():
    # Calculate the ttl until 3 AM the next day for CRON job
    #make sure this is utc 
    now = datetime.now()
    next_day = now + timedelta(days=1)
    next_3am = next_day.replace(hour=3, minute=0, second=0, microsecond=0)
    ttl = next_3am - now
    return ttl

#DB connection
# Initialize connection.
@st.cache_resource(ttl=get_ttl(), show_spinner = "Creating Connection...")
def init_connection():
    return st.connection("postgresql",type="sql")

conn = init_connection()

@st.cache_data(ttl=get_ttl(), show_spinner = "Creating Data...")
def query_db(query):
    #st.write("query_db")
    result = conn.query(query)
    return result



# Get latest dates from DB for all data sources
query = '''
    SELECT 
        (SELECT MAX(date) FROM student.de10_ja_weather) AS max_weather_date,
        (SELECT MIN(date) FROM student.de10_ja_weather) AS min_weather_date,
        (SELECT MAX(time) FROM student.de10_ja_earthquake) AS max_earthquake_time,
        (SELECT MAX(time) FROM student.de10_ja_natural_disasters) AS max_natural_disasters_time,
        (SELECT MAX(date) FROM student.de10_ja_neo) AS max_neo_date,
        (SELECT MAX(date) FROM student.de10_ja_apod) AS max_apod_date
'''

dates = query_db(query)

# Convert to datetime objects
max_weather_date = datetime.strptime(dates['max_weather_date'][0], '%Y-%m-%d').strftime('%Y-%m-%d')
min_weather_date = datetime.strptime(dates['min_weather_date'][0], '%Y-%m-%d').strftime('%Y-%m-%d')
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
        "Places to analyse (data from capital cities):", 
        countries_df['country'],
        ['United Kingdom', 'Spain', 'Mexico'], max_selections = 5)
    
    today_date_datetime = datetime.strptime(today_date, '%Y-%m-%d')
    date_20_years_ago = date(today_date_datetime.year - 0 , 6, 1)

    date_range = st.date_input(
        "Select the years to analyse",
        (date_20_years_ago, datetime.strptime(max_weather_date, '%Y-%m-%d')),
        datetime.strptime(min_weather_date, '%Y-%m-%d'),
        datetime.strptime(max_weather_date, '%Y-%m-%d'),
        format="YYYY/MM/DD",
    )    

    button_press = st.button("Analyse", type="primary")
    if button_press:
        #st.metric("Temperature", "26 C", "4 C from last year")
        # Loop through each weather option selected
        country_ids = []
        for weather_option in weather_options:
            # Find corresponding country_id for the selected weather_option
            ids = countries_df.loc[countries_df['country'] == weather_option, 'country_id'].tolist()
            country_ids.extend(ids)
        
        all_weather_data = pd.DataFrame()  # List to hold all weather data

        #get sql data for selected countries
        for country_id in country_ids:
            query = f"""SELECT * FROM student.de10_ja_weather WHERE country_id = {country_id} AND DATE(date) BETWEEN '{date_range[0]}' AND '{date_range[1]}'ORDER BY date ASC;"""
            weather_data = query_db(query)
            all_weather_data = pd.concat([weather_data,all_weather_data], ignore_index=True)

        all_weather_data = all_weather_data.merge(countries_df[['country_id', 'country']], on='country_id', how='left')

        #plot metrics
        #st.metric("Temperature", "26 C", "4 C from last year")

        #weather plots
        fig_temp = px.line(all_weather_data, x='date', y='avg_temp_c', title='Average Temperature Over Time', color='country')
        fig_temp.update_layout(xaxis_title='Date', yaxis_title='Average Temperature (°C)')
        st.plotly_chart(fig_temp)

        fig_precipitation = px.bar(all_weather_data, x='date', y='precipitation_mm', title='Daily Precipitation Over Time', color='country')
        fig_precipitation.update_layout(xaxis_title='Date', yaxis_title='Precipitation (mm)')
        st.plotly_chart(fig_precipitation)

        fig_wind = px.line(all_weather_data, x='date', y='avg_wind_speed_kmh', title='Average Wind Speed Over Time', color='country')
        fig_wind.update_layout(xaxis_title='Date', yaxis_title='Average Wind Speed (km/h)')
        st.plotly_chart(fig_wind)



    #earthquake plot 
    st.subheader(f"Earthquake Data")
    #query = f"SELECT * FROM student.de10_ja_earthquake where DATE(time) = '{max_earthquake_date}';"
    query = f"SELECT * FROM student.de10_ja_earthquake order by time desc limit 2;"
    earthquake_data = query_db(query)
    #st.write(earthquake_data)

    #map plot of daily quakes
    earthquake_fig = go.Figure(data=go.Scattergeo(
        lon = earthquake_data['longitude'],
        lat = earthquake_data['latitude'],
        text = earthquake_data['place'],
        mode = 'markers',
        marker = dict(
            size = 8,
            #opacity = 0.8,
            #reversescale = True,
            autocolorscale = False,
            line = dict(
                width=1,
                color='rgba(102, 102, 102)'
            ),
            colorscale = 'Reds',
            cmin = 5,
            color = earthquake_data['mag'],
            cmax = earthquake_data['mag'].max(),
            colorbar_title="Magnitude"
        )
        #marker_color = earthquake_data['mag']
        ))
    earthquake_fig.update_layout(
        title = f'Latest Earthquakes ({max_earthquake_date})',
        width=1000,  # Set the width of the figure
    )
    st.plotly_chart(earthquake_fig)


    #natural disaster plot
    st.subheader(f"Natural Disaster Data")
    #query = f"SELECT * FROM student.de10_ja_natural_disasters where DATE(time) = '{max_disaster_date}';"
    query = f"SELECT * FROM student.de10_ja_natural_disasters order by time desc limit 10;"
    disasters_data = query_db(query)
   
    #map plot of daily quakes
    # Define custom colors for each disaster type
    disaster_colors = {
        'Wildfires': 'yellow',
        'Severe Storms': 'green',
        'Volcanoes': 'red',
        'Sea and Lake Ice': 'blue'
    }

    # Add a 'color' column to the dataframe based on the disaster type
    disasters_data['color'] = disasters_data['type'].map(disaster_colors)
    # Initialize the figure
    disasters_fig = go.Figure()
    
    # Add a scatter trace for each disaster type
    for disaster_type, color in disaster_colors.items():
        filtered_data = disasters_data[disasters_data['type'] == disaster_type]
        disasters_fig.add_trace(go.Scattergeo(
            lon=filtered_data['longitude'],
            lat=filtered_data['latitude'],
            text=filtered_data['name'],
            mode='markers',
            marker=dict(
                size=8,
                color=color,  # Use the consistent color for this disaster type
                line=dict(
                    width=1,
                    color='rgba(102, 102, 102)'
                )
            ),
            name=disaster_type,  # This will appear in the legend
            hovertemplate=(
                '<b>%{text}</b><br>' +
                'Date: %{customdata[0]}<br>' +
                'Type: %{customdata[1]}<br>' +
                'Lat: %{lat}<br>' +
                'Lon: %{lon}<br>' +
                '<extra></extra>'
            ),
            customdata=filtered_data[['time', 'type']]
            
        ))

    minDisasterDtae = disasters_data['time'].min()[:10]
    disasters_fig.update_layout(
        title = f'Last 10 Natural Disasters ({minDisasterDtae} - {max_disaster_date})',
        #geo_scope='world',
        legend=dict(
        title="Disaster Types",
        itemsizing='constant',
        traceorder='normal',
        ),
        width=1000,  # Set the width of the figure
        
    )

    st.plotly_chart(disasters_fig)
    




#Space section
with tab2:
    st.header("Space Stats")
    query = f"SELECT * FROM student.de10_ja_apod order by date desc limit 1;" 
    #query = f"SELECT * FROM student.de10_ja_apod where DATE(date) = '{max_apod_date}';"
    apod_data = query_db(query)
    #st.write(apod_data)
    name, explanation, date, url = apod_data.iloc[0]
    st.subheader(f"Astronomy Picture of the Day (APOD)")
    st.image(url, caption=f'{name} ({date})', use_column_width=True)
    st.write(explanation)

    st.subheader(f"Near Earth Objects (NEO)")
    query = f"SELECT * FROM student.de10_ja_neo where DATE(date) = '{max_neo_date}';"
    neo_data = query_db(query)
    #st.write(neo_data)


    #NEO 3d Plot
    # Define a function to adjust astroid size based on diameter
    def adjust_marker_size(diameter):
        if diameter > 0.099:
            return diameter * 40  
        else:
            return diameter * 200  
    # Earth position
    earth_x, earth_y, earth_z = 0, 0, 0

    # Create random angles for the asteroid positions around Earth
    theta = np.linspace(0, 2 * np.pi, len(neo_data['miss_miles']))
    phi = np.linspace(0, np.pi, len(neo_data['miss_miles']))

    # Calculate the positions of the asteroids in 3D space
    xs = np.array(neo_data['miss_miles']) * np.cos(theta) * np.sin(phi)
    ys = np.array(neo_data['miss_miles']) * np.sin(theta) * np.sin(phi)
    zs = np.array(neo_data['miss_miles']) * np.cos(phi)

    # Create new NEO DataFrame
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
        text=neo_3d_df[neo_3d_df['is_hazardous'] == False].apply(lambda row:
                            f"Name: {row['name']}<br>"
                            f"NEO ID: {row['neo_id']}<br>"
                            f"Miss Distance: {row['miss_miles']} miles<br>"
                            f"Diameter: {row['diameter']} miles",
                            axis=1),
        showlegend=True  
    ))

    # Plot hazardous asteroids around Earth
    fig.add_trace(go.Scatter3d(
        x=neo_3d_df[neo_3d_df['is_hazardous'] == True]['x'],  # Filter for hazardous asteroids
        y=neo_3d_df[neo_3d_df['is_hazardous'] == True]['y'],
        z=neo_3d_df[neo_3d_df['is_hazardous'] == True]['z'],
        mode='markers',
        marker=dict(
            size=neo_3d_df.loc[neo_3d_df['is_hazardous'] == True, 'diameter'].apply(adjust_marker_size),  # Scale diameter for visibility
            color='red',  # Color for hazardous asteroids
            opacity=0.7
        ),
        name='Hazardous Asteroids',
        hoverinfo='text',
        text=neo_3d_df[neo_3d_df['is_hazardous'] == True].apply(lambda row:
                            f"Name: {row['name']}<br>"
                            f"NEO ID: {row['neo_id']}<br>"
                            f"Miss Distance: {row['miss_miles']} miles<br>"
                            f"Diameter: {row['diameter']} miles",
                            axis=1),
        showlegend=True 
    ))

    # Set axis limits based on the maximum distance
    max_distance = 1.2 * max(neo_data['miss_miles'])
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='Distance from Earth (miles)', range=[-max_distance, max_distance]),
            yaxis=dict(title='Distance from Earth (miles)',range=[-max_distance, max_distance]),
            zaxis=dict(title='Distance from Earth (miles)',range=[-max_distance, max_distance])
        ),
        title=f"3D Plot of Asteroids around Earth on {max_neo_date}",
        scene_aspectmode='cube', # Ensure the aspect ratio is equal
        autosize= True, 
        height = 500, 
        margin = dict(t = 50, b =30), 
        legend = dict(itemsizing = "constant"),
        scene_camera=dict(eye=dict(x=1.5, y=1.5, z=1.0), center=dict(x=0, y=0, z=-0.2))
    )

    st.plotly_chart(fig)


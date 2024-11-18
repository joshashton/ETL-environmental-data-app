import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from datetime import datetime, timedelta, date
# my module
import app_functions as appFunc

#get dates
today_date = datetime.today().strftime('%Y-%m-%d')

# setup connection for all queries
conn = appFunc.init_connection()

# inital setup queries
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

dates = appFunc.query_db(query, conn)

# Convert to formatted date strings
max_weather_date = dates['max_weather_date'][0].strftime('%Y-%m-%d')
min_weather_date = dates['min_weather_date'][0].strftime('%Y-%m-%d')
max_earthquake_date = dates['max_earthquake_time'][0].strftime('%Y-%m-%d')
max_disaster_date = dates['max_natural_disasters_time'][0].strftime('%Y-%m-%d')
max_neo_date = dates['max_neo_date'][0].strftime('%Y-%m-%d')
max_apod_date = dates['max_apod_date'][0].strftime('%Y-%m-%d')

# get daily temperature / avg_precip / avg_wind  cards for each country

# Define the query to fetch average weather data for each country for the latest date
query = f"""
    SELECT country_id, 
    AVG(avg_temp_c) AS avg_temp, 
    AVG(precipitation_mm) AS avg_precip, 
    AVG(avg_wind_speed_kmh) AS avg_wind 
    FROM student.de10_ja_weather
    WHERE date = '{max_weather_date}'
    GROUP BY country_id;
    """
monthly_weather_data = appFunc.query_db(query, conn)

# Read the CSV file into a DataFrame
countries_df = pd.read_csv('DataSetup/Data/capital_locations.csv')

st.title("Environmental Information Hub")

tab1, tab2 = st.tabs(["🌍 Earth", "🚀 Space"])


#Earth section
with tab1:
    st.header("Earth Stats")

    #To-Do
    # update countries csv in github
    # Make date picker responsive to countries ranges
    # Make it wide st.set_page_config(page_title="Ex-stream-ly Cool App",page_icon="🧊", layout="wide")
    # make date ranges neater on weather graphs
    # add buttons to maps 1 days - 1 week - 1 month - 1 year

    
    st.subheader("Historical Weather Analysis")

    weather_options = st.multiselect(
        "Places to analyse (data from capital cities):", 
        countries_df['country'],
        ['United Kingdom', 'Spain', 'Australia'], max_selections = 6)
    
    if weather_options:
        # Get chosen countries' IDs
        country_ids = []
        for weather_option in weather_options:
            # Find corresponding country_id for the selected weather_option
            ids = countries_df.loc[countries_df['country'] == weather_option, 'country_id'].tolist()
            country_ids.extend(ids)

        # Filter the monthly_weather_data for the selected countries
        avg_monthly_temp = monthly_weather_data[monthly_weather_data['country_id'].isin(country_ids)]
        avg_monthly_temp = avg_monthly_temp.merge(countries_df[['country_id', 'country']], on='country_id', how='left')

        # Display current monthly average temperature
        st.caption(":blue[Current Monthly Average Temperature]")
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]

        for index, row in avg_monthly_temp.iterrows():
            country_name = row['country']
            avg_temp = row['avg_temp']

            column = columns[index % 3]  # Cycle through columns
            with column:
                st.metric(f"{country_name}", f"{avg_temp:.2f} °C")

        # Display current monthly average precipitation
        st.caption(":blue[Current Monthly Average Precipitation]")
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]

        for index, row in avg_monthly_temp.iterrows():
            country_name = row['country']
            avg_precip = row['avg_precip']
            column = columns[index % 3]  # Cycle through columns
            with column:
                st.metric(f"{country_name}", f"{avg_precip:.2f} mm")

        # Display current monthly average wind speed
        st.caption(":blue[Current Monthly Average Wind Speed]")
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]

        for index, row in avg_monthly_temp.iterrows():
            country_name = row['country']
            avg_wind = row['avg_wind']

            column = columns[index % 3]  # Cycle through columns
            with column:
                st.metric(f"{country_name}", f"{avg_wind:.2f} km/h")
        today_date_datetime = datetime.strptime(today_date, '%Y-%m-%d')
        date_20_years_ago = date(today_date_datetime.year - 0 , 1, 1)

    
    query = '''
    SELECT forecast, "index", shortname, regionid,"from"
    FROM student.de10_ja_carbon
    WHERE DATE("from") = (SELECT MAX(DATE("from")) FROM student.de10_ja_carbon)
    ORDER BY forecast ASC;
    '''
    earthquake_data = appFunc.query_db(query, conn)

    # Define column names
    columns = ["forecast", "index", "shortname", "regionid"]

    # Convert to DataFrame
    df = pd.DataFrame(earthquake_data, columns=columns)

    # Define a function to color-code forecast levels
    def highlight_forecast(val):
        if val < 50:      # Low level (you can adjust the threshold)
            color = 'lightgreen'
        elif 50 <= val < 100:  # Moderate level
            color = 'yellow'
        else:             # High level
            color = 'salmon'
        return f'background-color: {color}'

    # Apply color-coding to the forecast column
    df_styled = df.style.applymap(highlight_forecast, subset=['forecast'])
    today_date = datetime.today().strftime('%Y-%m-%d')
    # Display the styled DataFrame in Streamlit
    st.subheader(f"UK Carbon Data ({today_date})")
    st.dataframe(df_styled)
    #st.write(earthquake_data)

    #earthquake plot 
    st.subheader(f"Earthquake Data")
    #query = f"SELECT * FROM student.de10_ja_earthquake where DATE(time) = '{max_earthquake_date}';"
    query = f"SELECT * FROM student.de10_ja_earthquake order by time desc limit 50;"
    earthquake_data = appFunc.query_db(query, conn)
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
        ),
        hovertemplate=(
                '<b>%{text}</b><br>' +
                'Date: %{customdata[0]}<br>' +
                'Magnitude: %{customdata[1]}<br>' +
                'Mag Type: %{customdata[2]}<br>' +
                'Lat: %{lat}<br>' +
                'Lon: %{lon}<br>' +
                '<extra></extra>'
            ),
        customdata=earthquake_data[['time', 'mag', 'magtype']]
        ))
    
    minEarthquakeDate = earthquake_data['time'].min().strftime('%Y-%m-%d')
    max_earthquake_date = earthquake_data['time'].max().strftime('%Y-%m-%d')

    earthquake_fig.update_layout(
        title = f'Last 50 Earthquakes ({minEarthquakeDate} - {max_earthquake_date})',
        width=1000,  # Set the width of the figure
    )

    st.plotly_chart(earthquake_fig)


    #natural disaster plot
    st.subheader(f"Natural Disaster Data")
    #query = f"SELECT * FROM student.de10_ja_natural_disasters where DATE(time) = '{max_disaster_date}';"
    query = f"SELECT * FROM student.de10_ja_natural_disasters order by time desc limit 50;"
    disasters_data = appFunc.query_db(query, conn)
   
    #map plot of daily quakes
    # Define custom colors for each disaster type
    disaster_colors = {
        'Wildfires': 'red',
        'Severe Storms': 'green',
        'Volcanoes': 'yellow',
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

    minDisasterDate = disasters_data['time'].min().strftime('%Y-%m-%d')
    max_disaster_date = disasters_data['time'].max().strftime('%Y-%m-%d')

    disasters_fig.update_layout(
        title = f'Last 50 Natural Disasters ({minDisasterDate} - {max_disaster_date})',
        # geo_scope='world',
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
    #query = f"SELECT * FROM student.de10_ja_apod order by date desc limit 1;" 
    query = f"SELECT * FROM student.de10_ja_apod where DATE(date) = '{max_apod_date}';"
    apod_data = appFunc.query_db(query, conn)
    #st.write(apod_data)
    name, explanation, date, url = apod_data.iloc[0]
    st.subheader(f"Astronomy Picture of the Day (APOD)")
    st.image(url, caption=f'{name} ({date})', use_column_width=True)
    st.write(explanation)

    st.subheader(f"Near Earth Objects (NEO)")
    query = f"SELECT * FROM student.de10_ja_neo where DATE(date) = '{max_neo_date}';"
    neo_data = appFunc.query_db(query, conn)
    #st.write(neo_data)


    #NEO 3d Plot
    # Define a function to adjust astroid size based on diameter
    def adjust_marker_size(diameter):
        if diameter > 0.099:
            return diameter * 20 
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


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


#DB connection
# Initialize connection.
conn = st.connection("postgresql",type="sql")
# Perform query.
df = conn.query('SELECT MAX(date) FROM student.de10_ja_apod;', ttl="10m")
#st.write(df)

#get dates
today_date = datetime.today().strftime('%Y-%m-%d')

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
        ["UK","USA", "France", "Thailand", "Peru"],
        ["UK"])

    if weather_options:
        st.metric("Temperature", "26 C", "4 C from last year")

#Space section
with tab2:
    st.header("Space Stats")
    query = f"SELECT * FROM student.de10_ja_apod ORDER BY date DESC LIMIT 1;"
    apod_data = conn.query(query, ttl="30m")
    st.write(apod_data)
    name, explanation, date, url = apod_data.iloc[0]
    st.subheader(f"Astronomy Picture of the Day (APOD)")
    st.image(url, caption=f'{name} ({date})', use_column_width=True)
    st.write(explanation)
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt # visualisation!
import plotly.express as px
import plotly.graph_objects as go

## Requests is the default library for asking python to talk to the web
import requests
## PPrint is 'Pretty Print' Which lets us print less offensive JSON
from pprint import pprint


st.title("Environmental Information Hub")
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
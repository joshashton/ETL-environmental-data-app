import streamlit as st
from datetime import datetime, timedelta
import pandas as pd


def get_ttl():
    # Calculate the ttl until 7 AM the next day for CRON job
    # make sure this is utc 
    now = datetime.now()
    next_day = now + timedelta(days=1)
    next_7am = next_day.replace(hour=7, minute=10, second=0, microsecond=0)
    ttl = next_7am - now
    return ttl


#DB connection
# Initialize connection.
@st.cache_resource(ttl=get_ttl(), show_spinner = "Creating Connection...")
def init_connection():
    return st.connection("postgresql",type="sql")


@st.cache_data(ttl=get_ttl(), show_spinner = False)
def query_db(query, _conn):
    #st.write("query_db")
    result = _conn.query(query)
    return result


# Function to aggregate data to monthly averages
def aggregate_monthly(data):
    
    data['date'] = pd.to_datetime(data['date'])
    monthly_data_list = []
    for country_id, group in data.groupby('country_id'):
       
        # Set time column as index
        monthly_group = group.set_index('date')
        # Convert only specific columns to numeric, setting errors='coerce' to handle non-numeric data
        monthly_group['avg_temp_c'] = pd.to_numeric(monthly_group['avg_temp_c'], errors='coerce')
        monthly_group['precipitation_mm'] = pd.to_numeric(monthly_group['precipitation_mm'], errors='coerce')
        monthly_group['avg_wind_speed_kmh'] = pd.to_numeric(monthly_group['avg_wind_speed_kmh'], errors='coerce')
        
        # Resample and calculate the mean for numeric columns
        numeric_columns = ['avg_temp_c', 'precipitation_mm', 'avg_wind_speed_kmh']
        monthly_group = monthly_group[numeric_columns].resample('M').mean()

        # Add country_id and country columns back
        monthly_group['country_id'] = country_id
        monthly_group['country'] = group['country'].iloc[0]  # Add country name to the monthly data
        monthly_group.reset_index(inplace=True)  # Reset index to include 'date' as a column
        monthly_data_list.append(monthly_group)       
  
    monthly_data = pd.concat(monthly_data_list).reset_index()
    return monthly_data

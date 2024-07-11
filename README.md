# Environmental Information Hub
A Streamlit application showcasing regularly updated environmental information 

See the Streamlit dashboard [here](https://etl-environmental-data-app.streamlit.app/)

## Description

The project involves using extract, transform and loading skills, updating a database routinely with a CRON job and using Streamlit as the front end to output the updated data. It is designed to monitor past and present environmental activity. 

The application has an earth and space section, each displaying different information involving the climate.

### Steps
CRONScript.py requests and extracts environmental data from multiple APIs:
* APOD - Astronomy picture of the day
* NEO - Near earth objects
* EONET - Earth Observatory Natural Event Tracker
* Weather
* Earthquake

The collected data is stored in their respective tables in the database. CRONScript.py sits on a job server running the script once a day collecting the updated data.

The Streamlit application reads from the database and displays the latest data.

### Built with
- Python (3.10)
- Streamlit (1.36.0)

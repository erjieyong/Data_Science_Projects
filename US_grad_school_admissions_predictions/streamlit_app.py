import streamlit as st
import requests
import json

# Title of the webpage
st.title("🎓 Graduate School Admissions")

# Get user inputs
gre = st.number_input("📚 GRE Score:", min_value=0, max_value=800, help="GRE score in the range 0 to 800") # int max value to allow only int inputs
gpa = st.number_input("✍️ GPA Score:", min_value=0.0, max_value=5.0, help="GPA in the range 0 to 5") # float max value to allow decimal inputs

# Display the inputs
user_input = {"gre":gre,"gpa":gpa}
st.write("User input:") # string that appears on your UI
st.write(user_input) # display user provided gre and gpa score inputs

# Code to post the user inputs to the API and get the predictions
# Paste the URL to your GCP Cloud Run API here!
api_url = 'https://grad-school-admission-6fz6u3cctq-as.a.run.app'
api_route = '/predict'

response = requests.post(f'{api_url}{api_route}', json=json.dumps(user_input)) # json.dumps() converts dict to JSON
predictions = response.json() # return dictionary with key 'predictions' & values are a list of predictions

# Add a submit button
if st.button("Submit"): # only display model predictions on UI if user clicks "Submit" button
    st.write(f"Prediction: {predictions['predictions'][0]}") # prediction values were stored in 'predictions' key of dict: predictions. [0] is to give prediction output 0/1 in a "unlisted" format since we're only sending user inputs for 1 row of X at a time

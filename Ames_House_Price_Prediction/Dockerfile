
# Use the official lightweight Python image from
# https://hub.docker.com/_/python
FROM python:3.8-slim 


# Copy all the files needed for the app to work
COPY inference.py .
COPY model/ ./model


#we have to do this for our project otherwise gcloud will throw error
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get -y install curl
RUN apt-get install libgomp1
# Install all the necessary libraries
RUN pip install -r ./model/requirements.txt



# Run the API!
CMD python inference.py


FROM python:3.8 

# Copy all the files needed for the app to work
COPY inference.py .
COPY requirements.txt .
COPY yolov7/ ./yolov7/

# Install all the necessary libraries
RUN apt-get update && apt-get install -y git ffmpeg libsm6 libxext6 libgl1-mesa-glx libgl1 libglib2.0-0 python3-opencv
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/facebookresearch/detectron2.git
RUN pip install opencv-python
RUN pip install opencv-contrib-python-headless

# Run the API!
CMD python inference.py

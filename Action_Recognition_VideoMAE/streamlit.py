import streamlit as st
from transformers import VideoMAEFeatureExtractor, VideoMAEForVideoClassification
import torch
import youtube_dl
# decord is a faster alternative of opencv
from decord import VideoReader, cpu 
import numpy as np
import os

# load videomae model from hugging face
feature_extractor = VideoMAEFeatureExtractor.from_pretrained("MCG-NJU/videomae-base-finetuned-kinetics")
model = VideoMAEForVideoClassification.from_pretrained("MCG-NJU/videomae-base-finetuned-kinetics")
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# outline
st.title("Action Recognition")
st.write("Github link: [github/erjieyong](https://github.com/erjieyong/Data_Science_Projects/tree/main/Action_Recognition_VideoMAE)")
form = st.form(key='form')
output = st.container()
_,video_container, _ = output.columns([1,3,1])

def predict(video_path):
  # video clip consists of 300 frames (10 seconds at 30 FPS)
  vr = VideoReader(video_path, num_threads=1, ctx=cpu(0)) 

  def sample_frame_indices(clip_len, frame_sample_rate, seg_len):
    # As the model only allow 16 frames as input
    # we will sample 16 frames from the video

    # get the total number of frames that our sample would span across
    converted_len = int(clip_len * frame_sample_rate)
    # get a randomised max frame of the video. This would be the last frame out of the 16 frame
    end_idx = np.random.randint(converted_len, seg_len)
    # get the first frame sample
    str_idx = end_idx - converted_len
    # evenly space out the frame between the start and end frame according to the frame sample rate
    index = np.linspace(str_idx, end_idx, num=clip_len)
    # ensure frames' index is within range and convert to numpy array
    index = np.clip(index, str_idx, end_idx - 1).astype(np.int64)

    # # we change the linspace to be spread from 20 to 80 percentile to capture more info across the video
    # index = np.linspace(seg_len*0.2, seg_len*0.8, num=clip_len)
    # index = np.clip(index, seg_len*0.2, seg_len*0.8 - 1).astype(np.int64)
    return index

  # we run vr.seek(0) to start the read
  vr.seek(0)
  # get the np array of frames
  index = sample_frame_indices(clip_len=16, frame_sample_rate=5, seg_len=len(vr))
  # get the frame rgb values as numpy (16 frames, height, width, rgb)
  buffer = vr.get_batch(index).asnumpy()

  # Prepare frames for feature extraction
  video = [buffer[i] for i in range(buffer.shape[0])]

  # extract features based on previous pipeline
  encoding = feature_extractor(video, return_tensors="pt")
  print(encoding.pixel_values.shape)

  pixel_values = encoding.pixel_values.to(device)

  # forward pass
  with torch.no_grad():
    outputs = model(pixel_values)
    logits = outputs.logits

  predicted_class_idx = logits.argmax(-1).item()

  return model.config.id2label[predicted_class_idx]




# form
url = form.text_input("Enter a youtube url. (youtube shorts included)", value = 'https://www.youtube.com/shorts/ZMr_OkDfUUg')
submit_form = form.form_submit_button(label = "Predict!")

if submit_form:
    with st.spinner('Downloading video'):
      # Download youtube video in specified format
      url = url.replace('shorts/','watch?v=')
      ydl_opts = {
        'format':'mp4[width<=?360][height<=?360]',
        'noplaylist': True,
        'outtmpl': 'test.mp4',
        'cachedir':False
        }
      ydl = youtube_dl.YoutubeDL(ydl_opts)
      try:
        os.remove('./test.mp4')
      except:
        pass
      finally:
        ydl.download([url])

      # Make predictions
      result = predict("test.mp4")

      # display video
      video_container.write("Output")
      video_container.video('test.mp4', format="video/mp4", start_time=0) 
      video_container.write(f"Video is showing someone **{result}**")
import time
import torch
import cv2
import numpy as np
from torchvision import transforms

from utils.datasets import letterbox
from utils.general  import non_max_suppression_kpt
from utils.plots    import output_to_keypoint, plot_skeleton_kpts

def pose_video(frame):
    mapped_img = frame.copy()
    # Letterbox resizing.
    img = letterbox(frame, input_size, stride=64, auto=True)[0]
    img_ = img.copy()
    # Convert the array to 4D.
    img = transforms.ToTensor()(img)
    # Convert the array to Tensor.
    img = torch.tensor(np.array([img.numpy()]))
    # Load the image into the computation device.
    img = img.to(device)
    
    # Gradients are stored during training, not required while inference.
    with torch.no_grad():
        t1 = time.time()
        output, _ = model(img)
        t2 = time.time()
        fps = 1/(t2 - t1)
        output = non_max_suppression_kpt(output, 
                                         0.25,    # Conf. Threshold.
                                         0.65,    # IoU Threshold.
                                         nc=1,   # Number of classes.
                                         nkpt=17, # Number of keypoints.
                                         kpt_label=True)
        
        output = output_to_keypoint(output)

    # Change format [b, c, h, w] to [h, w, c] for displaying the image.
    nimg = img[0].permute(1, 2, 0) * 255
    nimg = nimg.cpu().numpy().astype(np.uint8)
    nimg = cv2.cvtColor(nimg, cv2.COLOR_RGB2BGR)

    for idx in range(output.shape[0]):
        plot_skeleton_kpts(nimg, mapped_img, input_size, output[idx, 7:].T, 3)
        xmin, ymin = (output[idx,2] - output[idx,4]/2), (output[idx,3] - output[idx,5]/2)
        xmax, ymax = (output[idx,2] + output[idx,4]/2), (output[idx,3] + output[idx,5]/2)
        dx = int(xmax) - int(xmin)
        dy = int(ymax) - int(ymin)

    # in case there's not even 1 prediction at all
    if output.shape[0] == 0:
        dx, dy, xmin, ymin, xmax, ymax = 0,0,0,0,0,0
        
    return nimg, fps, dx, dy, xmin, ymin, xmax, ymax


# #------------------------------------------------------------------------------#
# # Change forward pass input size.
input_size = 256

#---------------------------INITIALIZATIONS------------------------------------#

# Select the device based on hardware configs.
if torch.cuda.is_available():
    device = torch.device("cuda:0")
else:
    device = torch.device("cpu")
print('Selected Device : ', device)

# device = torch.device("cpu")

# Load keypoint detection model.
weights = torch.load('yolov7-w6-pose.pt', map_location=device)
model = weights['model']
# Load the model in evaluation mode.
_ = model.float().eval()
# Load the model to computation device [cpu/gpu/tpu]
model.to(device)


vid_path = 'Media/default.mp4'

cap = cv2.VideoCapture(vid_path)

#check if videocapture not opened
if (cap.isOpened() == False):
    print('Error while trying to read video. Please check path again')
    
fps = int(cap.get(cv2.CAP_PROP_FPS))
ret, frame = cap.read()
h, w, _ = frame.shape
file_name = 'video_key.mp4'
out = cv2.VideoWriter('Media/' + file_name, cv2.VideoWriter_fourcc(*'mp4v'), fps, (input_size, input_size))

while True:
    ret, frame = cap.read()
    
    if not ret:
        print('Unable to read frame. Exiting ..')
        break

    img, fps, dx1, dy1, xmin, ymin, xmax, ymax = pose_video(frame)
    
    # Fall detection
    if (dy1 - dx1)< 0:
        # draw red bounding box
        cv2.rectangle(img,(int(xmin), int(ymin)),(int(xmax), int(ymax)),color=(255, 0, 0),
                thickness=5,lineType=cv2.LINE_AA)
        # draw red small upper box
        cv2.putText(img, 'FALL DETECTED!!!', (int(xmin), int(ymin)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (255, 0, 0), 2)

    # cv2.putText(img, 'FPS : {:.2f}'.format(fps_), (200, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv2.LINE_AA)
    # cv2.putText(img, 'YOLOv7', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv2.LINE_AA)

    # img[...,::-1] is to convert BGR to RGB
    cv2.imshow('Output', img[...,::-1])
    out.write(img[...,::-1])
    key = cv2.waitKey(1)
    if key == ord('q'):
      break


cap.release()
out.release()
cv2.destroyAllWindows()

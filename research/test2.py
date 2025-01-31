from __future__ import division
import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
from PIL import Image
import cv2

# This is needed since the notebook is stored in the object_detection folder.
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

CWD_PATH = os.getcwd()

# Path to frozen detection graph. This is the actual model that is used for the object detection.
MODEL_NAME = 'ssdlite_mobilenet_v2_coco_2018_05_09'
PATH_TO_CKPT = os.path.join(CWD_PATH, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90

##OTRA FORMA DE HACERLO (pero no esta funcionando ya que falta determinar 'PATH_TO_CKPT' y 'PATH_TO_LABELS'):
#sys.path.append('/home/francisco/anaconda2/envs/envFinal34/lib/python3.4/site-packages/tensorflow/models/research/object_detection')
#from utils import label_map_util
#from utils import visualization_utils as vis_util

# Path to frozen detection graph. This is the actual model that is used for the object detection.
# Note: Model used for SSDLite_Mobilenet_v2
#PATH_TO_CKPT = './model/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
#PATH_TO_LABELS = './data/mscoco_label_map.pbtxt'

#NUM_CLASSES = 90

# Path to frozen detection graph. This is the actual model that is used for the object detection.
# Note: Model used for SSDLite_Mobilenet_v2
#PATH_TO_CKPT = './model/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
#PATH_TO_LABELS = './data/mscoco_label_map.pbtxt'

#NUM_CLASSES = 90

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)

detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')

label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

def count_nonblack_np(img):
    """Return the number of pixels in img that are not black.
    img must be a Numpy array with colour values along the last axis.

    """
    return img.any(axis=-1).sum()


def detect_team(image, show = False):
    # define the list of boundaries
    boundaries = [
    ([17, 15, 100], [50, 56, 200]), #red
    ([25, 146, 190], [96, 174, 250]) #yellow
    ]
    i = 0
    for (lower, upper) in boundaries:
        # create NumPy arrays from the boundaries
        lower = np.array(lower, dtype = "uint8")
        upper = np.array(upper, dtype = "uint8")

        # find the colors within the specified boundaries and apply
        # the mask
        mask = cv2.inRange(image, lower, upper)
        output = cv2.bitwise_and(image, image, mask = mask)
        tot_pix = count_nonblack_np(image)
        color_pix = count_nonblack_np(output)
        ratio = color_pix/tot_pix
#         print("ratio is:", ratio)
        if ratio > 0.01 and i == 0:
            return 'red'
        elif ratio > 0.01 and i == 1:
            return 'yellow'

        i += 1
        
        if show == True:
            cv2.imshow("images", np.hstack([image, output]))
            if cv2.waitKey(0) & 0xFF == ord('q'):
              cv2.destroyAllWindows() 
    return 'not_sure'

## To View Color Mask
filename = 'image1.png'
image = cv2.imread(filename)
resize = cv2.resize(image, (640,360))
detect_team(resize, show=True)


#intializing the web camera device

out = cv2.VideoWriter('soccer_out.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 4, (640,360))

filename = 'videoplayback.mp4'
cap = cv2.VideoCapture(filename)

# Running the tensorflow session
with detection_graph.as_default():
  with tf.Session(graph=detection_graph) as sess:
   counter = 0
   while (True):
      ret, image_np = cap.read()
      counter += 1
      if ret:
          h = image_np.shape[0]
          w = image_np.shape[1]

      if not ret:
        break
      if counter % 1 == 0:
          # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
          image_np_expanded = np.expand_dims(image_np, axis=0)
          image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
          # Each box represents a part of the image where a particular object was detected.
          boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
          # Each score represent how level of confidence for each of the objects.
          # Score is shown on the result image, together with the class label.
          scores = detection_graph.get_tensor_by_name('detection_scores:0')
          classes = detection_graph.get_tensor_by_name('detection_classes:0')
          num_detections = detection_graph.get_tensor_by_name('num_detections:0')
          # Actual detection.
          (boxes, scores, classes, num_detections) = sess.run(
              [boxes, scores, classes, num_detections],
              feed_dict={image_tensor: image_np_expanded})
          # Visualization of the results of a detection.
          vis_util.visualize_boxes_and_labels_on_image_array(
              image_np,
              np.squeeze(boxes),
              np.squeeze(classes).astype(np.int32),
              np.squeeze(scores),
              category_index,
              use_normalized_coordinates=True,
              line_thickness=3,
              min_score_thresh=0.6)
        
          frame_number = counter
          loc = {}
          for n in range(len(scores[0])):
             if scores[0][n] > 0.60:
                # Calculate position
                ymin = int(boxes[0][n][0] * h)
                xmin = int(boxes[0][n][1] * w)
                ymax = int(boxes[0][n][2] * h)
                xmax = int(boxes[0][n][3] * w)

                # Find label corresponding to that class
                for cat in categories:
                    if cat['id'] == classes[0][n]:
                        label = cat['name']

                ## extract every person
                if label == 'person':
                    #crop them
                    crop_img = image_np[ymin:ymax, xmin:xmax]
                    color = detect_team(crop_img)
                    if color != 'not_sure':
                        coords = (xmin, ymin)
                        if color == 'red':
                             loc[coords] = 'PERU'
                        else:
                            loc[coords] = 'AUS'
                        
        ## print color next to the person
          for key in loc.keys():
            text_pos = str(loc[key])
            cv2.putText(image_np, text_pos, (key[0], key[1]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 0, 0), 2) # Text in black
      
      cv2.imshow('image', image_np)
      out.write(image_np)
       
      if cv2.waitKey(10) & 0xFF == ord('q'):
          cv2.destroyAllWindows()
          cap.release()
          break


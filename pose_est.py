from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

import io
import cv2
import copy
import base64
import numpy as np

from src import util
from src import model
from src.body import Body
from src.hand import Hand

body_estimation = Body('model/body_pose_model.pth')
hand_estimation = Hand('model/hand_pose_model.pth')

class Image(BaseModel):
    data: str
    hand_pose: int
    which_hand: int

app = FastAPI()

def recognize(base64_data, hand_pose, which_hand):
    # convert base64_data to the processable image first
    nparr = np.fromstring(base64.b64decode(base64_data), np.uint8)
    oriImg = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)

    candidate, subset = body_estimation(oriImg) # estimate body
    canvas = copy.deepcopy(oriImg) # copy original image for drawing
    canvas = util.draw_bodypose(canvas, candidate, subset) # draw bodypose
    
    if hand_pose==1:
        hands_list = util.handDetect(candidate, subset, oriImg) # detect hands
        all_hand_peaks = []
        for x, y, w, is_left in hands_list:
            if which_hand==1:
                cv2.rectangle(canvas, (x, y), (x+w, y+w), (0, 255, 0), 2, lineType=cv2.LINE_AA)
                cv2.putText(canvas, 'left' if is_left else 'right', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            peaks = hand_estimation(oriImg[y:y+w, x:x+w, :])
            peaks[:, 0] = np.where(peaks[:, 0]==0, peaks[:, 0], peaks[:, 0]+x)
            peaks[:, 1] = np.where(peaks[:, 1]==0, peaks[:, 1], peaks[:, 1]+y)
            if not is_left:
                peaks = hand_estimation(cv2.flip(oriImg[y:y+w, x:x+w, :], 1))
                peaks[:, 0] = np.where(peaks[:, 0]==0, peaks[:, 0], w-peaks[:, 0]-1+x)
                peaks[:, 1] = np.where(peaks[:, 1]==0, peaks[:, 1], peaks[:, 1]+y)
                print(peaks)
            all_hand_peaks.append(peaks)

        canvas = util.draw_handpose(canvas, all_hand_peaks)

    _, buffer = cv2.imencode('.jpg', canvas) # encode image for base64 response
    return base64.b64encode(buffer)

@app.post("/estimate/")
async def ocr_item(img: Image):
    return recognize(img.data, img.hand_pose, img.which_hand)

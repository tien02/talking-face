import cv2, os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import uuid

from src.sadtalker.utils.videoio import save_video_with_watermark 

def paste_pic(video_path, pic_path, crop_info, new_audio_path, full_video_path, extended_crop=False):

    if not os.path.isfile(pic_path):
        raise ValueError('pic_path must be a valid path to video/image file')
    
    # Load full image
    if pic_path.split('.')[-1].lower() in ['jpg', 'png', 'jpeg']:
        full_img = cv2.imread(pic_path)
    else:
        video_stream = cv2.VideoCapture(pic_path)
        ret, full_img = video_stream.read()
        video_stream.release()
        if not ret:
            raise ValueError("Could not read the video/image from pic_path")

    frame_h, frame_w = full_img.shape[:2]

    # Load crop frames one by one (lazy loading)
    video_stream = cv2.VideoCapture(video_path)
    fps = video_stream.get(cv2.CAP_PROP_FPS)
    crop_frames = []
    while True:
        ret, frame = video_stream.read()
        if not ret:
            break
        crop_frames.append(frame)
    video_stream.release()

    if len(crop_info) != 3:
        print("you didn't crop the image")
        return

    r_w, r_h = crop_info[0]
    clx, cly, crx, cry = crop_info[1]
    lx, ly, rx, ry = map(int, crop_info[2])

    if extended_crop:
        oy1, oy2, ox1, ox2 = cly, cry, clx, crx
    else:
        oy1, oy2, ox1, ox2 = cly + ly, cly + ry, clx + lx, clx + rx

    roi_w, roi_h = ox2 - ox1, oy2 - oy1
    location = ((ox1 + ox2) // 2, (oy1 + oy2) // 2)
    mask_shape = (roi_h, roi_w, 3)

    # Pre-create mask
    mask = 255 * np.ones(mask_shape, np.uint8)

    # Output video writer
    tmp_path = str(uuid.uuid4()) + '.mp4'
    out_tmp = cv2.VideoWriter(tmp_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_w, frame_h))

    # Define function for processing each frame
    def process_frame(frame):
        resized = cv2.resize(frame, (roi_w, roi_h))
        return cv2.seamlessClone(resized, full_img, mask, location, cv2.NORMAL_CLONE)

    # Use ThreadPoolExecutor for parallel seamless cloning
    with ThreadPoolExecutor(max_workers=8) as executor:
        for gen_img in executor.map(process_frame, crop_frames):
            out_tmp.write(gen_img)

    out_tmp.release()

    save_video_with_watermark(tmp_path, new_audio_path, full_video_path, watermark=False)
    os.remove(tmp_path)

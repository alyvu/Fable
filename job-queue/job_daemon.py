import torch
import os
import shutil
import numpy as np
from transformers import AutoModel
from transformers import logging
from PIL import Image

import psycopg2
import signal
import time

# suppresses unnecessary transformer warnings
logging.set_verbosity_error()

# creates tmp folder
tmpdir = './tmp'
os.makedirs(tmpdir, exist_ok=True)

# inits a keyboard interrupt signal handler
run = True
def signal_handler(signal, frame):
    global run
    print("Interrupt caught, exitting...")
    run = False
signal.signal(signal.SIGINT, signal_handler)

# inits postgresql connection
conn = psycopg2.connect('dbname=fable user=yuval password=a')
cur = conn.cursor()

# inits Magi model
model = AutoModel.from_pretrained("ragavsachdeva/magi", trust_remote_code=True).cuda()

def read_image_as_np_array(image_path):
    with open(image_path, "rb") as file:
        image = Image.open(file).convert("L").convert("RGB")
        image = np.array(image)
    return image

def process_job(job):
    id = job[0]
    print(f'Processing Job {id}')
    upload_ids = job[1]
    # creates tmp directory for this job to store output
    jobdir = f'{tmpdir}/{id}'
    os.makedirs(jobdir, exist_ok=True)
    # handles each upload one by one
    upload_ct = 1
    for upload_id in upload_ids:
        # fetches upload path and converts it to a numpy array
        cur.execute('select * from upload where id=(%s)',[upload_id])
        upload = cur.fetchall()[0]
        path = f'../cropper-flask/uploads/{upload[1]}'
        images=[read_image_as_np_array(path)]
        # passes the image data into the Magi model
        with torch.no_grad():
            results = model.predict_detections_and_associations(images)
            text_bboxes_for_all_images = [x["texts"] for x in results]
            ocr_results = model.predict_ocr(images, text_bboxes_for_all_images)
        # creates a tmp directory to store the crops
        cropdir = jobdir
        if len(upload_ids) > 1:
            cropdir = f'{jobdir}/{upload_ct}'
            os.makedirs(cropdir, exist_ok=True)
        # fetches the panel bounding box data and crops each panel
        panels = results[0]['panels']
        crop_ct = 1
        for panel in panels:
            left, top, right, bottom = panel
            bounds = (left, top, right, bottom)
            with open(path, "rb") as f:
                image = Image.open(f)
                cropped = image.crop(bounds)
                cropped.save(f"{cropdir}/crop_{crop_ct}.jpg")
            crop_ct += 1
        # stores the Magi output
        model.visualise_single_image_prediction(images[0], results[0], filename=f"{cropdir}/magi_analysis.png")
        model.generate_transcript_for_single_image(results[0], ocr_results[0], filename=f"{cropdir}/magi_transcript.txt")
        upload_ct += 1
    # zips the job data and stores it in the Flask static folder
    shutil.make_archive(f'../cropper-flask/static/downloads/{id}', 'zip', jobdir)
    print(f'Completed Job {id}')

# pings the job table for unprocessed jobs every 3 seconds
while run:
    # fetches an unprocessed job
    cur.execute('select * from job where status = 0 limit 1')
    job = cur.fetchone()
    if not job:
        continue
    # updates job status to in progress (status=1)
    cur.execute('update job set status=1 where id=%s', [job[0]])
    conn.commit()
    # processes the job
    process_job(job)
    # updates job status to complete (status=2)
    cur.execute('update job set status=2 where id=%s', [job[0]])
    conn.commit()
    time.sleep(10)
import os
from flask import Flask, request, jsonify, send_from_directory
from config import Config
from werkzeug.utils import secure_filename

import psycopg2
from psycopg2.extras import Json
from psycopg2.extensions import register_adapter

import pdb

app = Flask(__name__)
app.config.from_object(Config)

# create upload, static, and downloads folders from config
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOADS_FOLDER'], exist_ok=True)

# psql database init
register_adapter(dict, Json)
conn = psycopg2.connect('dbname=fable user=yuval password=a')
cur = conn.cursor()

@app.get('/api/jobs')
def get_jobs():
    cur.execute('select * from job order by id desc limit 5')
    jobs = cur.fetchall()
    return jsonify({'jobs': jobs})

@app.post('/api/create_job')
def create_job():
    if 'file' not in request.files:
        return jsonify({'Error': 'No file received'})
    # initializes job meta data
    job_name = 'Crop Job'
    # checks if a jobName param was received
    for item in request.values.items():
        if item[0] == 'jobName' and len(item[1]):
            job_name = item[1]
    meta = {
        'jobName': job_name,
        'filenames': []
    }
    # uploads each file to disk and stores a reference in psql
    upload_ids = []
    files = request.files.getlist('file')
    for file in files:
        # saves to /uploads folder
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # stores reference in upload table and stores the upload id
        cur.execute('insert into upload (name) values (%s) returning id', [filename])
        upload_id = cur.fetchone()[0]
        upload_ids.append(upload_id)
        # adds filename to job meta
        meta['filenames'].append(filename)
    # creates a new job to process the uploads
    cur.execute('insert into job (upload_ids, status, meta) values (%s, %s, %s)', [upload_ids, 0, meta])
    conn.commit()
    return jsonify({'Status': 200})
    
@app.get('/api/download/<path:id>')
def download_job(id):
    return send_from_directory(
        './static/downloads/', f'{id}.zip', as_attachment=True
    )

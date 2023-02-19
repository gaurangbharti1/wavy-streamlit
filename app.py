import streamlit as st
import requests
import json
import time
from tempfile import NamedTemporaryFile
import os

API_KEY = str(st.secrets["SIEVE_API_KEY"])

st.title("wav2lip")
st.markdown('Built by [Gaurang Bharti](https://twitter.com/gaurang_bharti) powered by [Sieve](https://www.sievedata.com)')

def send_to_transfersh(file, clipboard=True):
    """
    send file to transfersh, retrieve download link, and copy it to clipboard
    :param file: absolute path to file
    :param copy_to_clipboard: boolean value specifing if the download_link should be copied to clipboard
    :return: download_link
    """
    file_name = os.path.basename(file)

    url = 'https://transfer.sh/'
    file = {'{}'.format(file): open(file, 'rb')}
    response = requests.post(url, files=file)
    download_link = response.content.decode('utf-8')

    return download_link

def upload_local(path):
    link = (send_to_transfersh(path))
    return link

def check_status(url, interval, job_id):
    finished = False
    headers = {
        'X-API-Key': API_KEY
        }
    while True:
        response = requests.get(url, headers=headers)
        data = response.json()['data']
        for job in data:
            if job['id'] == job_id:
                print(job['status'])
                if job['status'] == 'processing':
                    print("processing")
                    time.sleep(interval)
                if job['status'] == 'finished':
                    print("finished")
                    finished = True
                    return finished
                if job['status'] == 'error':
                    return job['error']

def fetch_video(job_id):
    url = f"https://mango.sievedata.com/v1/jobs/{job_id}"
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    response = requests.get(url, headers = headers)
    data = response.json()
    url = data['data'][0]['url']
    return url

def send_data(video_link, audio_link):
    video_link = video_link.split("\n")
    audio_link = audio_link.split("\n")
    url = "https://mango.sievedata.com/v1/push"
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    } 
    data = {
        "workflow_name": "wavy",
        "inputs": {
            "video": {
                "url": video_link[0]},
            "audio": {
                "url": audio_link[0]}
            }
        }

    try:
        response = requests.post(url, headers=headers, json=data)
        if ('id') not in response.json():
            st.error(response.json()['description'])
            return False
        return (response.json()['id'])
    except Exception as e:
        return (f'An error occurred: {e}')

#Streamlit App

video_in = st.file_uploader("Video Upload")

audio_in = st.file_uploader("Audio Upload")

button1 = st.button("Wav2Lip")

if st.session_state.get('button') != True:

    st.session_state['button'] = button1

if st.session_state['button'] == True:
    if video_in:
        with NamedTemporaryFile(dir='.', suffix='.mp4', delete=False) as f:
            f.write(video_in.getbuffer())
            video_url = upload_local(f.name)
            f.close()
    if audio_in:
        with NamedTemporaryFile(dir='.', suffix='.wav', delete=False) as f:
            f.write(audio_in.getbuffer())
            audio_url = upload_local(f.name)
            f.close()
    job = send_data(video_url, audio_url)
    if job:
        with st.spinner("Processing video"):
            status = check_status('https://mango.sievedata.com/v1/jobs', 5, str(job))
            if status == True:
                video = fetch_video(job)
                st.video(video)
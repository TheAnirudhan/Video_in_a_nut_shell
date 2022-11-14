#imports
import moviepy.editor
import speech_recognition as sr 
import subprocess
import os 
import shutil
from pydub import AudioSegment
from pydub.silence import split_on_silence
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import requests
import time

class vid_summarizer:
    def __init__(self) -> None:
        self.ibm_key = 'IS9l69Fz2EZGNUD4-3vGsVKKSOrcoWrvBEqUGVZxnqbJ'
        self.ibm_url = 'https://api.eu-gb.speech-to-text.watson.cloud.ibm.com/instances/fcba1706-0ab4-484c-b296-2cd68151c6cc'
        self.authenticator = IAMAuthenticator(self.ibm_key)
        self.sst = SpeechToTextV1(authenticator=self.authenticator)
        self.sst.set_service_url(self.ibm_url)
        self.hft_key = "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"
        self.hft_url = 'https://api-inference.huggingface.co/models/facebook/bart-large-cnn'

    def vid2aud(self, file_dir):
        # Replace the parameter with the location of the video
        video = moviepy.editor.VideoFileClip(file_dir)
        audio = video.audio
        # Replace the parameter with the location along with filename
        audio.write_audiofile("audio.mp3")
        shutil.move("audio.mp3","static/files/audio.mp3")
        video.close()
        return True

    def ibm_stt(self):
        command = 'ffmpeg -i static/files/audio.mp3 -f segment -segment_time 250 -c copy static/files/a_chunks/%03d.mp3' #segmenting the audio
        subprocess.call(command, shell=True)
        # return "True"

        files =[]
        for filename in os.listdir('static/files/a_chunks/'):
            if filename.endswith(".mp3"):
                files.append('static/files/a_chunks/' + filename)
                print(filename)
        
        results=[]
        for filename in files:
            print(filename,time.localtime())
            with open(filename, 'rb') as f:
                res = self.sst.recognize(audio=f,content_type='audio/mp3', model='en-US_NarrowbandModel', 
                                inactivity_timeout=360).get_result()
                results.append(res)
        
        self.text = []
        for file in results:
            for result in file['results']:
                self.text.append(result['alternatives'][0]['transcript'].rstrip() + '\n')
        self.text = [i.replace('%HESITATION','') for i in self.text]
        return self.text

    def hft_summarizer(self, text):
        headers = {"Authorization": f"Bearer {self.hft_key}"}
        def query(payload):
            response = requests.post(self.hft_url, headers=headers, json=payload)
    #         print(headers)
            return response.json()
        text = '/n'.join(text)
        out = query({
            "inputs": text,
            "parameters": {"min_length" : 100,
                        "max_length" : 350,}
        })
        # out_text = '\n'.join([i[0]['summary_text'] for i in out])
        return out[0]['summary_text']

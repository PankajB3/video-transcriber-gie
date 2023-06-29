import openai
import os
import tempfile
import yt_dlp
import time
import mutagen

from flask import Flask, jsonify, request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain import OpenAI
from flask_cors import CORS
from moviepy.editor import *
from urllib.parse import urlparse, parse_qs
from pydub import AudioSegment
from mutagen.mp3 import MP3
from moviepy.editor import *


os.environ["OPENAI_API_KEY"] = ""

app = Flask(__name__)
cors = CORS(app)

# segment the mp3 into smaller versions of 10 minutes
def segments_one_minute(mp3_file_path, video_id):
    # mp3_size_sec = os.path.getsize(mp3_file_path)
    # print("size of mp3 file", mp3_size_sec)
    # whisper_default_size = 25*1024*1024 #25 MB in bytes
    mp3_audio = AudioFileClip(mp3_file_path)
    flag = False
    index = 60
    start = 0
    counter = 0
    n = round(mp3_audio.duration)
    path = os.path.join(os.getcwd(), f'{video_id}')
    os.mkdir(path)
    
    while(True):
        audio_clip = AudioFileClip(mp3_file_path)
        if index >= n:
            flag = True
            index = n
        
        temp = audio_clip.subclip(start, index)
        temp_file = os.path.join(os.getcwd()+f'/{video_id}/{counter}.mp3')
        temp.write_audiofile(filename=temp_file)
        temp.close()
        counter+=1
        start = index
        audio_clip.close()
        
        if flag:
            break;
        
        index += 60
    return path        
    
    
def transcribe_video(mp3_file_path, video_id):
    #calculate size of mp3
    mp3file_size_bytes = os.path.getsize(mp3_path)
    print("size of mp3 file", mp3file_size_bytes)
    whisper_default_size = 25*1024*1024 #25 MB in bytes
    
    if(mp3file_size_bytes < whisper_default_size): # check if given file is smaller than 25 MB
        openai.api_key=""
        with open(mp3_file_path,"rb") as audio_file:
            transcript = openai.Audio.transcribe(
                file=audio_file,
                model="whisper-1",
                response_format="text",
                language="en"
            )
        return transcript
    else:
        transcribed_text = []
        segmented_files_dir = segments_one_minute(mp3_file_path, video_id) # function call for segmennting video into small segments
        files_list = os.listdir(segmented_files_dir)
        for index in range(len(files_list)):
            audio_segment_path = os.path.join(segmented_files_dir,f'{index}.mp3')
            # audio_clip = AudioFileClip(audio_segment_path)
            # duration = audio_clip.duration
            # audio_clip.close()
            openai.api_key=""
            with open(audio_segment_path,"rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    file=audio_file,
                    model="whisper-1",
                    response_format="text",
                    language="en"
                )
            # print(index + " => " + transcript)
            transcribed_text.append(transcript)
        return transcribed_text

# def videoToMp3(url):
#     print(url)
#     # creating temporary directory for storing mp3 files
#     temp_Dir = tempfile.TemporaryDirectory()
    
#     # extracting id from youtube video
#     query = urlparse(url).query
#     params = parse_qs(query)
#     video_id = params["v"][0]
    
#     print(video_id)
    
#     # download the video from youtube using URL
#     yt_video = YouTube(url)
    
#     print("#################\n\n 43 \n\n###################")
    
#     # extracting audio from video file  
#     audio_stream = yt_video.streams.filter(progressive=True, file_extension='mp4').order_by().desc().first().download()
#     print("#################\n\n 47 \n\n###################")
    
#     # audio_stream.download(output_path=temp_Dir)
    
#     print(audio_stream)
#     print("#################\n\n 48 \n\n###################")
    
#     # convert audio output to mp3
#     audio_path = os.path.join(temp_Dir, audio_stream.default_filename)
#     audio_clip = AudioFileClip(audio_path)
#     audio_clip.write_audiofile(os.path.join(temp_Dir, f"{video_id}.mp3"))
    
#     # storing path of mp3 file
#     mp3_file_path = f"{temp_Dir}/{video_id}.mp3"
    
#     return mp3_file_path

def yt_dlt_method(url):
    print(url)
    # creating temporary directory for storing mp3 files
    temp_Dir = tempfile.TemporaryDirectory()
    
    # extracting id from youtube video
    query = urlparse(url).query
    params = parse_qs(query)
    video_id = params["v"][0]
    
    URLS = [url]

    # %(id)s is a placeholder that will be replaced by the video ID of the YouTube video. It is obtained from the information extracted by yt-dlp.
    # %(ext)s is a placeholder that will be replaced by the file extension of the downloaded video/audio file. This allows the downloaded file to keep its original extension.

    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': os.path.join(os.getcwd(), '%(id)s.%(ext)s'),
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(URLS)
        temp_file_path = os.path.join(os.getcwd(), f'{video_id}.mp3')
    
    return temp_file_path

# url = "https://www.youtube.com/watch?v=eGPRo82ry0I"
url ="https://www.youtube.com/watch?v=QdDoFfkVkcw"
# loader = YoutubeLoader.from_youtube_url(url)
# result = loader.load()
# print(result)


# mp3_path = videoToMp3(url)
# video_summary = transcribe_video(mp3_path)
# os.remove(mp3_path)
# print(video_summary)


mp3_path = yt_dlt_method(url)
print("################\n\n 177 \n\n###################")
transcript_video = transcribe_video(mp3_path, "QdDoFfkVkcw")
print(transcript_video)


# video_summary = transcribe_video(mp3_path)
# os.remove(mp3_path)
# print(video_summary)
# print(mp3_file_path)

@app.route('/')
def index():
    return 'Welcome To YouTube Transcriber'

# @app.route('/add-tutorial')
# def add_tutorial():
#      query = urlparse(url).query
    # params = parse_qs(query)
    # video_id = params["v"][0]
#     mp3_path = videoToMp3("url")
#     video_summary = transcribe_video(mp3_path)
#     os.remove(mp3_path)
#     return jsonify(video_summary)




if __name__ == '__main__':
    app.run()

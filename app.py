import openai
import os
import tempfile
import yt_dlp
import shutil
import io

from flask import Flask, jsonify, request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain import OpenAI
from flask_cors import CORS
from moviepy.editor import *
from urllib.parse import urlparse, parse_qs
from pydub import AudioSegment
from mutagen.mp3 import MP3
from moviepy.editor import *
from dotenv import load_dotenv, dotenv_values
from pinecone_store import *

directory = "subtitle"

# loading environment variables
load_dotenv()
opena_ai_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
cors = CORS(app)

# segment the mp3 into smaller versions of 10 minutes
async def segments_one_minute(mp3_file_path, video_id):
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
            # index = n
            # print(index)
        
        if flag:
            break;            
        
        temp = audio_clip.subclip(start, index)
        temp_file = os.path.join(os.getcwd()+f'/{video_id}/{counter}.mp3')
        temp.write_audiofile(filename=temp_file)
        temp.close()
        counter+=1
        start = index
        audio_clip.close()
        
        index += 60
    return path        
    
    
async def transcribe_video(mp3_file_path, video_id):
    try:
        #calculate size of mp3
        mp3file_size_bytes = os.path.getsize(mp3_file_path)
        print("size of mp3 file", mp3file_size_bytes)
        whisper_default_size = 25*1024*1024 #25 MB in bytes
        
        if(mp3file_size_bytes < whisper_default_size): # check if given file is smaller than 25 MB
            openai.api_key=opena_ai_key
            with open(mp3_file_path,"rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    file=audio_file,
                    model="whisper-1",
                    response_format="text",
                    language="en"
                )
            os.remove(mp3_file_path)
            return transcript
        else:
            transcribed_text = []
            segmented_files_dir = await segments_one_minute(mp3_file_path, video_id) # function call for segmennting video into small segments
            files_list = os.listdir(segmented_files_dir)
            for index in range(len(files_list)):
                audio_segment_path = os.path.join(segmented_files_dir,f'{index}.mp3')
                openai.api_key=opena_ai_key
                with open(audio_segment_path,"rb") as audio_file:
                    transcript = openai.Audio.transcribe(
                        file=audio_file,
                        model="whisper-1",
                        response_format="text",
                        language="en"
                    )
                # print(index + " => " + transcript)
                transcribed_text.append(transcript)
            shutil.rmtree(segmented_files_dir)
            os.remove(mp3_file_path)
            return transcribed_text
    except Exception as e:
        return e

# returns the path of mp3 file downloaded of the given url
async def yt_dlt_method(url):
    try:
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
            #See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download(URLS)
            temp_file_path = os.path.join(os.getcwd(), f'{video_id}.mp3')
        
        return temp_file_path
    except Exception as e:
        return e
    
    
# writing the transcript output in a text file
async def store_subtitle_txt(video_id, transcript):
    try:
        file_name = f"{video_id}.txt"
        # check type of transcript paramter
        if isinstance(transcript, list):
            video_script = "\n".join(transcript)
        else:
            video_script = transcript
        
        subtitle_file_path = os.path.join(directory, file_name)
        # check if directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Write to the file
        with io.open(subtitle_file_path, "w", encoding="utf-8") as file:
            file.write(video_script)
        return True
    except IOError:
        raise Exception("File error occurred")
    except FileNotFoundError:
        raise Exception("File Not Found")
    except FileExistsError:
        raise Exception("File Already Exists")
        
# url = "https://www.youtube.com/watch?v=eGPRo82ry0I"
# # url ="https://www.youtube.com/watch?v=QdDoFfkVkcw"
# # url = "https://www.youtube.com/watch?v=h0DHDp1FbmQ"


# ***********************************************************
# fetching video-id out of url
# query = urlparse(url).query
# params = parse_qs(query)
# video_id = params["v"][0]

# mp3_path = yt_dlt_method(url)    # path of mp3 file downloaded out of url

# # creating a thread for transcribe_video function
# transcript_video = transcribe_video(mp3_path, video_id) 

# print("\n##############################\n",transcript_video) 

# video_txt = transcript_video 


# store_subtitle_txt(video_id, video_txt)  

# # store data in pincone
# store_transcribe_to_pinecone(url, video_id)
# ***********************************************************


@app.route('/')
def index():
    return 'Welcome To YouTube Transcriber'

@app.route('/add-tutorial' , methods=['POST'])
async def add_tutorial():
    try:
        data = request.get_json() # Fetch the request body as JSON data
        url = data["url"]
        query = urlparse(url).query
        params = parse_qs(query)
        video_id = params["v"][0]
    
        mp3_path = await yt_dlt_method(url)
        
        # creating a thread for transcribe_video function
        transcript_video = await transcribe_video(mp3_path, video_id) 
        
        video_txt = transcript_video
        
        flag = await store_subtitle_txt(video_id, video_txt)
        
        # store data in pincone
        await store_transcribe_to_pinecone(url, video_id)
        
        return jsonify("Tutorial Uploaded")
    except Exception as e:
        return jsonify("Error In Uploading. Try Again Later", e)



if __name__ == '__main__':
    app.run()

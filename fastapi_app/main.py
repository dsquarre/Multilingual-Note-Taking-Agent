import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile
#from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from faster_whisper import WhisperModel
import os
from fpdf import FPDF
import google.generativeai as genai
from pydub import AudioSegment
import asyncio


UPLOAD_DIR = Path()
filepath = Path()


highlight = ""
model = None
gemini_model = None

app = FastAPI()

app.mount("/static",StaticFiles(directory="build/static"),name="static")



""" headers = {'Access-Control-Expose-Headers': 'Content-Disposition','Access-Control-Allow-Origin':'http://localhost:3000'}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=headers
) """

@app.on_event("startup")  
async def startup_event():
    global gemini_model,model
    #select base or small for better transcription
    model = WhisperModel("tiny", device="cpu", compute_type="int8", local_files_only=False)
    
    # Configure Gemini API (replace with your API key)
    genai.configure(api_key="AIzaSyBDYZL3Bxqfz50K2PJLg6qol0Y86RHmJzE")
    gemini_model = genai.GenerativeModel('gemini-1.5-flash') #gemini model for your api key

def transcribe(file):
    global model
    segments, _ = model.transcribe(file)
    return segments

async def transcribe_chunk(file):
    loop = asyncio.get_running_loop()
    transcript = await loop.run_in_executor(None,transcribe,file)
    return transcript
    

def split_audio(file):
    """  from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token="") #only read access
    diarization = pipeline(file) 
    i = 0
    for turn,_,speaker in diarization.itertracks(yield_label=True):
        chunk = audio[turn.start:turn.end]
        i+=1
        out_path = f"./chunk_{i}.mp3"
        chunk.export(out_path,format="mp3",bitrate= "48k")
        chunks.append(out_path)
    return chunks """
    audio=AudioSegment.from_file(file)
    chunks = []
    chunk_length = 4*60*1000
    for i, start in enumerate(range(0,len(audio),chunk_length)):
         chunk = audio[start:start +chunk_length] 
         out_path = f"chunk_{i}.mp3"
         chunk.export(out_path,format="mp3",bitrate= "48k")
         chunks.append(out_path)
    return chunks.copy()
    

async def get_summary(text):
    prompt = f"""This is the transcribed text of a meeting. Transcript could be multilingual so autocorrect and translate if something doesnt make sense. Dont add any asterisks, just use spaces and newlines, since your reponse text will directly be written into a pdf as text.
                 Return a well descriptive summary of what was said in the meeting, who said what, and final takeaways/action points and conclusions.
            Transcribed text:{text}"""
    return await gemini_model.generate_content_async(prompt)

async def get_highlights(transcript):
    prompt = f"""
    Given the following transcribed text with timestamps(in seconds), identify and return only the segments containing action items, important points, or tasks. If any other language is detected, then *keep it as it is* and also add your english translation in brackets.
    Include the timestamp and text for each highlighted segment. Correct the grammatical errors if any. If no action items then just return a one line summary of what was said in the audio.
    Dont add any asterisks in your response ,just use spaces and newlines, because your generated content will be directly displayed on screen to user. just use newlines and spaces.
    Transcribed text:
    {transcript}
    """
    return await gemini_model.generate_content_async(prompt)

@app.post("/upload/")
async def getAudio(file: UploadFile):
    global model, highlight, UPLOAD_DIR, gemini_model
    audio = await file.read()
    save_to = UPLOAD_DIR / f"{file.filename}"
    inputfile = None
    with open(save_to,'wb') as f:
        f.write(audio)
    os.system(f"ffmpeg -i '{save_to}' -vn -ar 16000 -ac 1 -b:a 48k input.mp3 -y")
    os.remove(save_to)
    inputfile = "input.mp3"
    # Transcribe audio
    chunks = split_audio(inputfile)
    transcriptions = await asyncio.gather(*[transcribe_chunk(file) for file in chunks])

    text = ""
    transcript = ""
    start = 0
    end = 0
    offset = 0
   
    for segment_list in transcriptions:
        for segment in segment_list:
            text += segment.text + "\n"
            end = offset + segment.end - segment.start
            start = offset
            offset = end 
            hour = start/3600
            min = (hour - (int)(hour))*60
            sec = (min - (int)(min))*60
            timestamp = f"{(int)(hour)}"+"."+f"{(int)(min)}"+"."+f"{(int)(sec)}"
            hour = end/3600
            min = (hour - (int)(hour))*60
            sec = (min - (int)(min))*60
            timestamp =timestamp +" : "+ f"{(int)(hour)}"+"."+f"{(int)(min)}"+"."+f"{(int)(sec)}"
            transcript = transcript+f"{timestamp}-{segment.text}\n"
    for path in chunks:
        os.remove(path)
    transcribe = FPDF()
    transcribe.add_font('NotoSansTC', '', '/usr/share/fonts/truetype/noto/NotoSansTC-Regular.ttf', uni=True)
    transcribe.set_font('NotoSansTC', '', 10)
    transcribe.add_page()
    transcribe.multi_cell(0, 10, f"{transcript}")
    transcribe.output(UPLOAD_DIR / "transcript.pdf")

    
    
    summary_resp, highlight_resp = await asyncio.gather(
    get_summary(text),
    get_highlights(transcript) )

    summary = summary_resp.text
    highlight = highlight_resp.text.replace("\n", "<br>")
    # Create PDF
    outputfile = UPLOAD_DIR / "summary.pdf"
    summarize = FPDF()
    
    summarize.add_page()
    

    summarize.add_font('NotoSans', '', '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf', uni=True)

    summarize.set_font('NotoSans', '', 11)
    
    # save summary into pdf
    summarize.multi_cell(0, 10, f"{summary}")
    summarize.output(outputfile)

    
    # Clean up
    os.remove(inputfile)
    
    return "transcribed"

@app.get("/result/summary")
async def give():
    global UPLOAD_DIR
    path = UPLOAD_DIR / "summary.pdf"
    return FileResponse(path=path, filename="summary.pdf", media_type='application/pdf')

@app.get("/result/transcript")
async def give():
    global UPLOAD_DIR
    path = UPLOAD_DIR / "transcript.pdf"
    return FileResponse(path=path, filename="transcript.pdf", media_type='application/pdf')


@app.get("/result/highlights")
async def send():
    global highlight
    return highlight

@app.get("/")
def read_index():
    return FileResponse("build/index.html")
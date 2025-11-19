import os
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from pydub import AudioSegment
import uuid

app = FastAPI()

# 임시 폴더 경로
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

def cleanup_files(*file_paths):
    """작업이 끝나면 파일을 삭제하는 함수"""
    for path in file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Deleted: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

@app.post("/convert")
async def convert_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # 1. 고유 파일명 생성
    unique_id = str(uuid.uuid4())
    input_filename = f"{unique_id}_input_{file.filename}"
    output_filename = f"{unique_id}.mp3"
    
    input_path = os.path.join(TEMP_DIR, input_filename)
    output_path = os.path.join(TEMP_DIR, output_filename)

    # 2. 파일 저장
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. 변환 (FFmpeg 엔진 사용)
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3", bitrate="128k")
    except Exception as e:
        # 실패 시 원본 삭제 후 에러 리턴
        cleanup_files(input_path)
        return {"error": str(e)}

    # 4. 응답 후 삭제 예약 (Background Tasks)
    # 파일 전송이 완료된 '직후'에 원본과 결과물 모두 삭제합니다.
    background_tasks.add_task(cleanup_files, input_path, output_path)

    # 5. 파일 전송
    return FileResponse(
        output_path, 
        media_type="audio/mpeg", 
        filename="converted.mp3"
    )
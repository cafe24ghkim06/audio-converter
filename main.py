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
    # 1. 원본 파일명 파싱 (확장자 분리)
    original_filename = file.filename
    # 파일명에 확장자가 있다면 분리, 없다면 그대로 사용
    if "." in original_filename:
        filename_no_ext = original_filename.rsplit(".", 1)[0]
    else:
        filename_no_ext = original_filename
    
    # 다운로드될 파일 이름 설정 (한글 등 특수문자 포함 가능)
    final_filename = f"{filename_no_ext}.mp3"

    # 2. 내부 처리용 고유 파일명 생성 (충돌 방지용)
    unique_id = str(uuid.uuid4())
    input_temp_name = f"{unique_id}_input"
    output_temp_name = f"{unique_id}.mp3"
    
    input_path = os.path.join(TEMP_DIR, input_temp_name)
    output_path = os.path.join(TEMP_DIR, output_temp_name)

    # 3. 파일 저장
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. 변환 (FFmpeg 엔진 사용)
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3", bitrate="128k")
    except Exception as e:
        cleanup_files(input_path)
        return {"error": str(e)}

    # 5. 응답 후 삭제 예약
    background_tasks.add_task(cleanup_files, input_path, output_path)

    # 6. 파일 전송 (여기서 filename을 지정하면 원본 이름으로 다운로드됨)
    return FileResponse(
        output_path, 
        media_type="audio/mpeg", 
        filename=final_filename
    )

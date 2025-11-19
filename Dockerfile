# 1. 파이썬 환경 불러오기
FROM python:3.9-slim

# 2. 필수 프로그램(FFmpeg) 설치 - 이게 핵심!
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 3. 작업 폴더 설정
WORKDIR /app

# 4. 파일 복사 및 라이브러리 설치
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 서버 실행 (포트 80)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
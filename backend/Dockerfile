# Dockerfile cho Bridge Section Auditor Pro (Backend)
FROM python:3.10-slim

WORKDIR /app

# Cài đặt LibreOffice Headless để convert Word sang PDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-common \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code và templates
COPY schemas.py tcvn_engine.py aashto_engine.py eurocode_engine.py report_generator.py ai_assistant.py main.py ./
COPY templates/ ./templates/

# Khởi tạo thư mục output
RUN mkdir -p reports

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Hướng dẫn Build & Run:
# docker build -t bridge-auditor-backend .
# docker run -d -p 8000:8000 -v $(pwd)/reports:/app/reports bridge-auditor-backend

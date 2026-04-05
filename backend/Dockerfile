FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files into a 'backend' package so imports like 'from backend.config' work
COPY . ./backend/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

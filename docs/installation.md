# Инструкция по установке OCR Web Service

## Системные требования

### Минимальные требования
- **ОС:** Astra Linux или Windows Server 2019
- **RAM:** 4GB (рекомендуется 8GB+)
- **Диск:** 10GB свободного места
- **CPU:** 2 ядра (рекомендуется 4+)

### Программное обеспечение
- Docker 24.0+
- Docker Compose 2.24+
- Python 3.11+ (для локальной разработки)
- Node.js 20+ (для локальной разработки)

## Установка через Docker (рекомендуется)

### 1. Клонирование проекта

```bash
cd /opt
git clone <repository-url> ocr-web-service
cd ocr-web-service
```

### 2. Загрузка моделей PaddleOCR

**Важно:** Модели должны быть загружены до запуска Docker контейнеров.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python ../scripts/download_models.py
deactivate
```

Модели будут сохранены в `backend/models/`.

### 3. Настройка окружения

Создайте файл `.env` в корне проекта:

```bash
cp .env.example .env
```

Отредактируйте `.env` при необходимости (по умолчанию настройки подходят для большинства случаев).

### 4. Запуск сервисов

```bash
cd docker
docker-compose up -d
```

Это запустит:
- Redis (очередь задач)
- Backend API (FastAPI)
- Celery Worker (обработка OCR)
- Frontend (React)
- Nginx (reverse proxy)

### 5. Проверка работы

Откройте браузер и перейдите по адресу:
```
http://localhost
```

Проверка API:
```bash
curl http://localhost/api/v1/health
```

Ожидаемый ответ: `{"status": "healthy"}`

### 6. Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

## Установка на Astra Linux

### Дополнительные шаги для Astra Linux

1. Установка Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

2. Перезагрузите систему или выполните:

```bash
newgrp docker
```

3. Продолжите с шага 1 основной инструкции.

## Установка на Windows Server 2019

### Дополнительные шаги для Windows Server

1. Установите Docker Desktop for Windows:
   - Скачайте с https://www.docker.com/products/docker-desktop
   - Запустите установщик
   - Перезагрузите систему

2. Включите WSL 2 (если требуется):

```powershell
wsl --install
```

3. Продолжите с шага 1 основной инструкции, используя PowerShell.

## Локальная разработка (без Docker)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Загрузка моделей
python ../scripts/download_models.py

# Запуск Redis (в отдельном терминале)
redis-server

# Запуск Celery worker (в отдельном терминале)
celery -A app.tasks.celery_app worker --loglevel=info

# Запуск API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173

## Обновление

```bash
cd ocr-web-service
git pull
cd docker
docker-compose down
docker-compose build
docker-compose up -d
```

## Удаление

```bash
cd docker
docker-compose down -v  # -v удаляет volumes с данными
```

## Решение проблем

### Порты заняты

Если порт 80 занят, измените в `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "8080:80"  # Вместо "80:80"
```

### Недостаточно памяти

Увеличьте лимиты памяти в `docker-compose.yml`:

```yaml
celery-worker:
  deploy:
    resources:
      limits:
        memory: 4G
```

### Модели не загружаются

Убедитесь, что есть доступ к интернету при первой загрузке моделей. После загрузки интернет не требуется.

## Поддержка

При возникновении проблем проверьте логи:

```bash
docker-compose logs backend
docker-compose logs celery-worker
```

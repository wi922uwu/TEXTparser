# Руководство по развертыванию

## Архитектура системы

```
┌─────────────┐
│   Nginx     │  Reverse Proxy (порт 80)
└──────┬──────┘
       │
   ┌───┴────┬──────────┐
   │        │          │
┌──▼───┐ ┌─▼──────┐ ┌─▼──────┐
│Frontend│Backend │ │ Redis  │
│(React) │(FastAPI)│ │        │
└────────┘└────┬───┘ └────────┘
               │
          ┌────▼────────┐
          │Celery Worker│
          │   (OCR)     │
          └─────────────┘
```

## Компоненты

1. **Nginx** — веб-сервер и reverse proxy
2. **Frontend** — React приложение (статические файлы)
3. **Backend** — FastAPI REST API
4. **Redis** — брокер сообщений для Celery
5. **Celery Worker** — асинхронная обработка OCR задач

## Развертывание в production

### 1. Подготовка сервера

#### Astra Linux

```bash
# Обновление системы
sudo apt-get update
sudo apt-get upgrade -y

# Установка Docker
sudo apt-get install -y docker.io docker-compose

# Настройка Docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Установка git
sudo apt-get install -y git
```

#### Windows Server 2019

1. Установите Docker Desktop for Windows
2. Установите Git for Windows
3. Перезагрузите систему

### 2. Клонирование проекта

```bash
# Создайте директорию для проекта
sudo mkdir -p /opt/ocr-service
sudo chown $USER:$USER /opt/ocr-service
cd /opt/ocr-service

# Клонируйте репозиторий
git clone <repository-url> .
```

### 3. Загрузка моделей OCR

**Критически важно:** Модели должны быть загружены до первого запуска.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python ../scripts/download_models.py
deactivate
```

Модели занимают ~500MB и загружаются один раз.

### 4. Настройка окружения

Создайте файл `.env`:

```bash
cp .env.example .env
nano .env
```

Настройте параметры:

```env
# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# File limits
MAX_FILE_SIZE=52428800  # 50MB
FILE_RETENTION_HOURS=24

# OCR settings
OCR_LANGUAGE=ru
USE_GPU=false

# Celery workers
CELERY_WORKERS=2  # Количество параллельных обработчиков
```

### 5. Настройка Nginx (опционально)

Если нужно изменить порт или добавить SSL:

Отредактируйте `docker/nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl;
    server_name ocr.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # ... остальная конфигурация
}
```

### 6. Запуск сервисов

```bash
cd docker
docker-compose up -d
```

Проверка статуса:

```bash
docker-compose ps
```

Все сервисы должны быть в состоянии "Up".

### 7. Проверка работоспособности

```bash
# Проверка API
curl http://localhost/api/v1/health

# Проверка frontend
curl http://localhost

# Проверка логов
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

## Мониторинг

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f celery-worker
docker-compose logs -f redis
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование диска
docker system df
```

### Мониторинг очереди Celery

```bash
# Подключение к Redis
docker exec -it ocr-redis redis-cli

# Проверка длины очереди
LLEN celery

# Выход
exit
```

## Масштабирование

### Увеличение количества Celery workers

Отредактируйте `docker-compose.yml`:

```yaml
celery-worker:
  deploy:
    replicas: 4  # Количество worker процессов
```

Или запустите дополнительные workers:

```bash
docker-compose up -d --scale celery-worker=4
```

### Ограничение ресурсов

```yaml
celery-worker:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

## Резервное копирование

### Что нужно сохранять

1. **Модели PaddleOCR** — `backend/models/`
2. **Конфигурация** — `.env`, `docker-compose.yml`
3. **Загруженные файлы** (опционально) — Docker volume `upload_data`

### Создание резервной копии

```bash
# Остановка сервисов
docker-compose down

# Резервное копирование
tar -czf ocr-backup-$(date +%Y%m%d).tar.gz \
  backend/models/ \
  .env \
  docker-compose.yml

# Запуск сервисов
docker-compose up -d
```

### Восстановление

```bash
# Распаковка
tar -xzf ocr-backup-20240322.tar.gz

# Запуск
docker-compose up -d
```

## Обновление

### Обновление кода

```bash
cd /opt/ocr-service
git pull

# Пересборка контейнеров
cd docker
docker-compose down
docker-compose build
docker-compose up -d
```

### Обновление зависимостей

```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate

# Frontend
cd frontend
npm update

# Пересборка
cd ../docker
docker-compose build
docker-compose up -d
```

## Безопасность

### Рекомендации

1. **Firewall:** Откройте только необходимые порты
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **SSL/TLS:** Используйте HTTPS в production
3. **Обновления:** Регулярно обновляйте систему и Docker образы
4. **Логи:** Настройте ротацию логов
5. **Доступ:** Ограничьте доступ к серверу

### Настройка HTTPS

1. Получите SSL сертификат (Let's Encrypt, корпоративный CA)
2. Поместите сертификаты в `docker/nginx/ssl/`
3. Обновите `nginx.conf` (см. выше)
4. Перезапустите Nginx:
   ```bash
   docker-compose restart nginx
   ```

## Решение проблем

### Сервис не запускается

```bash
# Проверка логов
docker-compose logs backend

# Проверка конфигурации
docker-compose config

# Пересоздание контейнеров
docker-compose down
docker-compose up -d --force-recreate
```

### Медленная обработка

1. Увеличьте количество Celery workers
2. Проверьте загрузку CPU/RAM
3. Оптимизируйте настройки PaddleOCR

### Ошибки памяти

```bash
# Увеличьте лимиты памяти
docker-compose down
# Отредактируйте docker-compose.yml
docker-compose up -d
```

### Очистка старых данных

```bash
# Очистка старых файлов (выполняется автоматически)
# Ручная очистка:
docker exec ocr-backend python -c "from app.storage.file_manager import FileManager; FileManager().cleanup_old_files()"
```

## Производительность

### Рекомендуемые характеристики сервера

| Нагрузка | CPU | RAM | Диск |
|----------|-----|-----|------|
| Низкая (1-5 пользователей) | 2 ядра | 4GB | 20GB |
| Средняя (5-20 пользователей) | 4 ядра | 8GB | 50GB |
| Высокая (20+ пользователей) | 8 ядер | 16GB | 100GB |

### Оптимизация

1. **SSD диск** для uploads/results
2. **Больше RAM** для кэширования моделей
3. **Больше CPU** для параллельной обработки
4. **GPU** (опционально) для ускорения OCR

## Автоматизация

### Systemd service (Linux)

Создайте `/etc/systemd/system/ocr-service.service`:

```ini
[Unit]
Description=OCR Web Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ocr-service/docker
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
sudo systemctl enable ocr-service
sudo systemctl start ocr-service
```

### Автоматическое обновление

Создайте cron задачу для еженедельного обновления:

```bash
crontab -e
```

Добавьте:

```cron
0 2 * * 0 cd /opt/ocr-service && git pull && cd docker && docker-compose up -d --build
```

## Контакты

При возникновении проблем с развертыванием обратитесь к технической поддержке.

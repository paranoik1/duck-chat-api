import argparse
import asyncio
import logging
import uvicorn
from utils import generate_models, needs_editing
from service import app

# Настройка аргументов командной строки с argparse
parser = argparse.ArgumentParser(description="Запуск сервиса")
parser.add_argument('--host', type=str, default='127.0.0.1', help='Хост для сервера (по умолчанию 127.0.0.1)')
parser.add_argument('--port', type=int, default=8000, help='Порт для сервера (по умолчанию 8000)')
parser.add_argument('--log-level', type=str, default='info', help='Уровень логирования (например, debug, info, warning, error, critical)')
parser.add_argument('-f', action='store_true', help='Пропустить проверку needs_editing и запустить generate_models без условий')

args = parser.parse_args()

# Настройка логирования
logging.basicConfig(level=args.log_level.upper(),
                    format="%(filename)s: " 
                    "%(levelname)s: " 
                    "%(funcName)s(): "
                    "%(message)s",)
logger = logging.getLogger(__name__)

# Если требуется, выполнить generate_models
if args.f or not needs_editing():
    logger.info("Запуск generate_models...")
    asyncio.run(generate_models())

# Запуск приложения
logger.info(f"Запуск сервера на {args.host}:{args.port}...")
uvicorn.run(app, host=args.host, port=args.port)

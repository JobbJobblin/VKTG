import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from config.log_config import LoggerConfig
from pathlib import Path


def setup_logging(log_name: str,
                  debug: bool = LoggerConfig.IS_DEBUG) -> logging.Logger:
    LoggerConfig.MAIN_LOG_NAME = log_name if log_name is not None else LoggerConfig.MAIN_LOG_NAME
    logger = logging.getLogger(LoggerConfig.MAIN_LOG_NAME)  # TODO:
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Проверка папки с логами
    log_folder = LoggerConfig.LOG_DIR
    filename = f"{log_folder}/{log_name}.log"
    log_path = Path.cwd() / log_folder
    log_path.mkdir(parents=True, exist_ok=True)

    # Обработчик логов для файла
    file_handler = TimedRotatingFileHandler(
        filename=filename,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Обработчик для сообщений для пользователя
    user_notice_handler = logging.StreamHandler(sys.stdout)
    user_notice_handler.setLevel(logging.INFO)
    user_notice_handler.setFormatter(formatter)  # TODO: user_formatter

    logger.addHandler(file_handler)
    logger.addHandler(user_notice_handler)

    return logger


# Возвращает дочерний логгер
def get_logger(name: str):
    return logging.getLogger(f"{LoggerConfig.MAIN_LOG_NAME}.{name}")

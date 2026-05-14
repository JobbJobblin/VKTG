import sys

from PyQt6.QtWidgets import QApplication

from config.logger_settings import setup_logging
from config.parser_settings import set_parser
from services.gui.gui import MainWindow


def main() -> None:
    # Входящие параметры
    parser = set_parser()
    args = parser.parse_args()

    # Инициализация логгера
    logger = setup_logging(args.log_name, args.debug)
    logger.info("Запуск главного приложения")
    # logger.info("Название файла логов: ")
    # logger.info("main-log" if args.log_name is None else f"\"{args.log_name}\"")
    logger.info("Уровень логирования: ")
    logger.info("INFO" if args.debug is False else f"DEBUG")

    # Инициализация gui
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def setup_windows_encoding():
    """ Функция принудительной установки кодировки для windows """
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)


if __name__ == "__main__":
    setup_windows_encoding()
    main()

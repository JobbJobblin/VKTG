from queue import Queue
from typing import Optional

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QGroupBox
)

from config.logger_settings import get_logger
from services.gui.gui_support import PyQtWorkerThread
from services.update_processor import UpdateProcessor
from services.vk_longpoll import VkLongPoll


class MainWindow(QMainWindow):
    """ Главное окно приложения """

    def __init__(self) -> None:
        super().__init__()

        # Логгер
        self.logger = get_logger("main_window")
        self.logger.debug("Инициализация пользовательского интерфейса")

        # Основные параметры окна
        self.setWindowTitle("ADL3")
        self.setGeometry(100, 100, 800, 600)

        # Общая очередь для потоков
        self.queue: Queue = Queue(maxsize=1000)

        # Исполнители (producer и consumer)
        self.producer_worker: VkLongPoll = VkLongPoll(event_queue=self.queue)
        self.consumer_worker: UpdateProcessor = UpdateProcessor(event_queue=self.queue)

        # Потоки
        self.producer_thread: Optional[PyQtWorkerThread] = None
        self.consumer_thread: Optional[PyQtWorkerThread] = None

        # Настройка UI
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """ Настройка пользовательского интерфейса """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Группа управления
        control_group = QGroupBox("Главная")
        control_layout = QVBoxLayout()

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Запуск")
        self.stop_btn = QPushButton("⏹ Выключение")
        self.stop_btn.setEnabled(False)

        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        control_layout.addLayout(buttons_layout)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # Группа статистики
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()

        self.producer_status_label = QLabel("ВК: Не запущен")
        self.consumer_status_label = QLabel("Обработчик: Не запущен")

        stats_layout.addWidget(self.producer_status_label)
        stats_layout.addWidget(self.consumer_status_label)

        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # Группа логов
        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout()

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        log_layout.addWidget(self.log_widget)

        # Кнопка очистки логов
        clear_logs_btn = QPushButton("Очистить")
        log_layout.addWidget(clear_logs_btn)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Подключаем кнопку очистки
        clear_logs_btn.clicked.connect(self.log_widget.clear)

    def _connect_signals(self) -> None:
        """Подключение всех сигналов и слотов"""
        # Кнопки управления
        self.start_btn.clicked.connect(self.start_system)
        self.stop_btn.clicked.connect(self.stop_system)

        # Сигналы producer
        self.producer_worker.inform.connect(self._log_message)
        self.producer_worker.error.connect(self._log_error)
        self.producer_worker.started.connect(self._on_producer_started)
        self.producer_worker.finished.connect(self._on_producer_finished)

        # Сигналы consumer
        self.consumer_worker.inform.connect(self._log_message)
        self.consumer_worker.error.connect(self._log_error)
        self.consumer_worker.started.connect(self._on_consumer_started)
        self.consumer_worker.finished.connect(self._on_consumer_finished)

    # ========== Управление системой ==========

    @pyqtSlot()
    def start_system(self) -> None:
        """Запуск всей системы"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Создаем потоки для воркеров
        self.producer_thread = PyQtWorkerThread(self.producer_worker)
        self.consumer_thread = PyQtWorkerThread(self.consumer_worker)

        # Запускаем потоки
        self.producer_thread.start()
        self.consumer_thread.start()

        self._log_message("🚀 Взлетаем...")

    @pyqtSlot()
    def stop_system(self) -> None:
        """Остановка всей системы"""
        self._log_message("🛑 Остановка...")

        # Останавливаем воркеры и ждем завершения потоков
        if self.producer_thread:
            self.producer_thread.stop()
        if self.consumer_thread:
            self.consumer_thread.stop()

        # Сбрасываем
        self.producer_thread = None
        self.consumer_thread = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    # ========== Обработчики сигналов ==========

    @pyqtSlot(str)
    def _log_message(self, message: str) -> None:
        """ Вывод обычного сообщения в лог + логирование """
        self.log_widget.append(f"[INFO] {message}")
        self.logger.info(message)
        # Автопрокрутка вниз
        cursor = self.log_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_widget.setTextCursor(cursor)

    @pyqtSlot(str)
    def _log_error(self, error: str) -> None:
        """ Вывод ошибки в лог (красным) """
        self.log_widget.append(f'<span style="color: red;">[ERROR] {error}</span>')
        self.logger.error(error)

    @pyqtSlot()
    def _on_producer_started(self) -> None:
        """ Producer запущен """
        self.producer_status_label.setText("ВК: ✅ Запущен")

    @pyqtSlot()
    def _on_producer_finished(self) -> None:
        """ Producer завершил работу """
        self.producer_status_label.setText("ВК: ⏹ Выключен")
        self._check_all_finished()

    @pyqtSlot()
    def _on_consumer_started(self) -> None:
        """ Consumer запущен """
        self.consumer_status_label.setText("Обработчик: ✅ Запущен")

    @pyqtSlot()
    def _on_consumer_finished(self) -> None:
        """ Consumer завершил работу """
        self.consumer_status_label.setText("Обработчик: ⏹ Выключен")
        self._check_all_finished()

    def _check_all_finished(self) -> None:
        """ Проверяет, завершили ли работу оба исполнителя """
        if (not self.producer_worker.is_running and
                not self.consumer_worker.is_running):
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def closeEvent(self, event) -> None:
        """ Обработка закрытия окна """
        self._log_message("Закрываю приложение...")
        self.stop_system()
        event.accept()

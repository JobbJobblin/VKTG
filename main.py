import sys # Только для доступа к аргументам командной строки
import time

from PyQt6.QtWidgets import \
    QApplication, QLabel, QLineEdit, QWidget, QPushButton, QGridLayout, QMessageBox
from PyQt6.QtCore import pyqtSlot, QThreadPool, Qt, pyqtSignal, QThread

from handlers.VKParse import VkPars

class Worker(QThread):
    """
    Класс, выполняющий бесконечный процесс.
    """
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_running = True

    def run(self):
        while True:
            try:
                self.progress_signal.emit('Всё работает!')
                VkPars()
            except Exception as e:
                self.progress_signal.emit('Ошибка соединения. Перезапускаюсь...')
                time.sleep(2)

    def stop(self):
        self.is_running = False

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("AD Logistics")
        self.setFixedSize(300, 300)
        self.initUI()

    def Booper(self):
        print("boop")

    def initUI(self):

        self.StartButt = QPushButton("Запустить")
        self.StartButt.setCheckable(True)
        self.StartButt.clicked.connect(self.Booper)
        self.StartButt.clicked.connect(self.start_process)
        self.StartButt.clicked.connect(self.Booper)
        self.StartButt.clicked.connect(self.displayMessageBoxStart)

        self.exit_button = QPushButton("Остановить")
        self.exit_button.setCheckable(True)
        self.exit_button.clicked.connect(self.stop_process)

        self.label = QLabel("Процесс не запущен")

        layout = QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.label, 1, 0)
        layout.addWidget(self.StartButt, 3, 0)
        #layout.addWidget(self.exit_button, 3, 2)

        self.show()

    def displayMessageBoxStart(self):
        QMessageBox.about(self, "Внимание", "Полетели \(;_;)/")

    def start_process(self):
        self.worker = Worker()
        self.worker.progress_signal.connect(self.update_label)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()
        self.StartButt.setEnabled(False)
        self.exit_button.setEnabled(True)
        self.label.setText("Процесс запущен...")

    def update_label(self, text):
        """
        Обновляет текст метки.
        """
        self.label.setText(text)

    def stop_process(self):
        """
        Останавливает рабочий поток.
        """
        if self.worker:
            self.worker.stop()
            self.qexit_button.setEnabled(False)
            self.label.setText("Остановка процесса...")

    def on_worker_finished(self):
      """
      Вызывается по завершении работы worker-а.
      """
      self.label.setText("Процесс остановлен.")
      self.StartButt.setEnabled(True)
      self.worker = None # Сбрасываем worker

    def closeEvent(self, event):
        print('CLOSING')
        MainWindow.stop()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
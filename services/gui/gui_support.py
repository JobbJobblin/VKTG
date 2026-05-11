import asyncio
from abc import ABC, abstractmethod, ABCMeta
from typing import Optional, List

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtCore import QThread


class QObjectABCMeta(type(QObject), ABCMeta):
    """
    Метакласс, объединяющий QObject и ABC.
    Решает конфликт метаклассов.
    """
    pass


class AsyncPyQtWorker(QObject, ABC, metaclass=QObjectABCMeta):
    """
    Абстрактный класс дла асинхронного исполнителя PyQt.
    Запускает свой event-loop для своего потока.
    """
    # Список сигналов PyQt
    started: pyqtSignal = pyqtSignal()
    finished: pyqtSignal = pyqtSignal()
    error: pyqtSignal = pyqtSignal(str)
    inform: pyqtSignal = pyqtSignal(str)

    def __init__(self, name: str = "AsyncPyQtWorkerDescendant") -> None:
        """
        :param name: имя исполнителя
        """
        super().__init__()
        self.name: str = name
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._tasks: List[asyncio.Future] = []
        self._main_task: asyncio.Task = None
        self._stop_event: asyncio.Event = asyncio.Event()
        self._running: bool = False

    @abstractmethod
    async def _main_loop(self) -> None:
        """
        Основной асинхронный цикл работы.

        Пример реализации:
            async def _main_loop(self):
                while not self._stop_event.is_set():
                    await self. ...
                    except asyncio.CancelledError:
                        break
        """

    def run_event_loop(self) -> None:
        """
        Запускает event-loop для потока
        """
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self._stop_event.clear()

            self.started.emit()

            self._main_task = self._loop.create_task(
                self._main_loop(),
                name=f"{self.name}_main"
            )

            self.inform.emit(f"[{self.name}] Event-loop запущен")
            self._running = True
            self._loop.run_until_complete(self._main_task)

        except asyncio.CancelledError:
            self.inform.emit(f"[{self.name}] Задача отменена")
        except Exception as e:
            self.error.emit(f"[{self.name}] Ошибка: {e}")
        finally:
            self._shutdown()

    def _shutdown(self) -> None:
        """
        Завершение event loop.
        Отменяет задачи и закрывает loop.
        """
        if not self._loop or self._loop.is_closed():
            return

        try:
            if self._main_task and not self._main_task.done():
                self._main_task.cancel()

            pending = asyncio.all_tasks(self._loop)

            if pending:
                self.inform.emit(
                    f"[{self.name}] Отмена {len(pending)} незавершённых задач..."
                )

                for task in pending:
                    task.cancel()

                try:
                    self._loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                except Exception:
                    pass

        except Exception as e:
            self.error.emit(f"[{self.name}] Ошибка при остановке: {e}")
        finally:
            # Закрываем event loop
            try:
                self._loop.close()
            except Exception:
                pass

            self._loop = None
            self._main_task = None
            self._tasks.clear()
            self._running = False

            self.finished.emit()
            self.inform.emit(f"[{self.name}] Event-loop остановлен")

    def schedule_coroutine(self, coro) -> Optional[asyncio.Future]:
        """
        Добавляет корутину к event-loop

        :param coro: Корутина для выполнения
        :return: Объект Task или None, если event-loop не запущен
        """

        if self._loop and self._loop.is_running():
            task: asyncio.Future = asyncio.run_coroutine_threadsafe(coro, self._loop)  # TODO ????
            self._tasks.append(task)
            task.add_done_callback(lambda t: self._tasks.remove(t))
            return task
        else:
            self.error.emit(f"[{self.name}] Event-loop не запущен. Невозможно добавить корутину на исполнение.")
            return None

    def stop(self) -> None:
        """
        Останавливает event-loop и отменяет ВСЕ задачи.
        """
        self._running = False
        self.inform.emit(f"[{self.name}] Отправлен сигнал остановки")

        if self._loop and self._loop.is_running():
            # 1. Устанавливаем флаг остановки
            self._loop.call_soon_threadsafe(self._stop_event.set)

            # 2. Отменяем ВСЕ задачи (включая главную)
            self._loop.call_soon_threadsafe(self._cancel_all_tasks)
        else:
            # Если loop не запущен, просто устанавливаем флаг
            self._stop_event.set()

    def _cancel_all_tasks(self) -> None:
        """
        Отменяет все задачи в event-loop.
        Вызывается в потоке event-loop.
        """
        if not self._loop or self._loop.is_closed():
            return

        # Отменяем главную задачу
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()

        # Отменяем все остальные задачи
        for task in asyncio.all_tasks(self._loop):
            if task is not self._main_task and not task.done():
                task.cancel()

        self.inform.emit(f"[{self.name}] Все задачи отменены")

    @property
    def is_running(self) -> bool:
        """ Возвращает состояние исполнителя (True - запущен, False - не запущен) """
        return self._running

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """ Возвращает event-loop исполнителя (если запущен) """
        return self._loop


class PyQtWorkerThread(QThread):
    """
    Вспомогательный класс-обёртка в QThread для AsyncPyQtWorker
    """

    def __init__(self, worker: AsyncPyQtWorker, parent=None) -> None:
        """

        :param worker: Экземпляр AsyncPyQtWorker для запуска
        :param parent: Родительский QObject. #TODO ???
        """
        super().__init__(parent)
        self.worker: AsyncPyQtWorker = worker

    def run(self) -> None:
        """ Запуск event-loop исполнителя в текущем потоке """
        self.worker.run_event_loop()

    def stop(self) -> None:
        """ Остановка исполнителя и ожидание завершения работы потока """
        self.worker.stop()
        if self.isRunning():
            self.quit()
from __future__ import annotations  # Postponed annotation calculation

import asyncio
from dataclasses import dataclass, asdict
from queue import Queue

import aiohttp

from config.config_reader import config
from config.logger_settings import get_logger
from services.connection_consistency import NetworkMonitor, ReSession
from model.vk_response_dcs import Updates
from .gui.gui_support import AsyncPyQtWorker


class VkLongPoll(AsyncPyQtWorker):
    """
    Асинхронный класс-producer. Получает события через long-poll от вк и складывает их в очередь.
    """

    def __init__(self, event_queue: Queue) -> None:
        """ :param event_queue: Очередь для задач """
        super().__init__("VkLongPoll")  # Передаём имя родителю
        self.logger = get_logger(self.name)  # "VkLongPoll"
        self.inform.emit(f"[{self.name}] Инициализация {self.name}")

        self.vpn_monitor = NetworkMonitor()
        self.session_manager = ReSession(self.vpn_monitor)
        self._restart_event: asyncio.Event | None = None
        self.queue = event_queue

    async def _main_loop(self) -> None:
        """ Запуск цикла получения событий """
        self.inform.emit(f"[{self.name}] Запускаю {self.name}...")

        # Привязываем события к текущему event loop, иначе при перезапуске будет спам
        self._restart_event = asyncio.Event()
        self._stop_event = asyncio.Event()

        server_params = await self._get_long_poll_params()

        tasks = [
            asyncio.create_task(self._longpoll_cycle(server_params), name='long-poll'),
            asyncio.create_task(self._network_watcher(), name='vpn_check'),
        ]

        try:
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            self.error.emit(f"[{self.name}] Критическая ошибка: {e}")
        finally:
            await self.session_manager.close()

    async def _longpoll_cycle(self, server_params: ServerParams) -> None:
        """ Основой цикл опроса вк """
        # Внешний try для корректного закрытия сессии aiohttp
        try:
            while not self._stop_event.is_set():
                await self._try_longpoll(server_params)
        finally:
            await self.session_manager.close()

    async def _longpoll_sequence(self,
                                 server_params: ServerParams,
                                 wait: int = 25) -> dict | None:
        """ Метод единичного запроса событий (long-poll) """
        url = f"{server_params.server}" \
              f"?act=a_check" \
              f"&key={server_params.key}" \
              f"&ts={server_params.ts}" \
              f"&wait={wait}"

        session = await self.session_manager.get_session()
        request_task = asyncio.create_task(
            self._do_request(session, url),
            name='lp_request'
        )

        stop_task= asyncio.create_task(
            self._stop_event.wait(),
            name='stop_listener'
        )

        restart_task= asyncio.create_task(
            self._restart_event.wait(),
            name='restart_listener'
        )

        done, pending = await asyncio.wait(
            [request_task, restart_task, stop_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if request_task in done:
            try:
                return request_task.result()
            except asyncio.CancelledError:
                return None

        if stop_task in done:
            self.inform.emit(f"[{self.name}] Получена команда остановки от пользователя")
            return None

        if restart_task in done:
            self.inform.emit(f"[{self.name}] Включен впн. Перезапуск сессии")
            if not request_task in done:
                request_task.cancel()
            return None


    async def _do_request(self, session: aiohttp.ClientSession, url: str) -> dict | None:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None


    async def _get_long_poll_params(self) -> ServerParams:
        """ Получение базовых параметров для long-poll'а """
        self.logger.debug("Отправлен запрос на получение параметров для long-poll")
        async with aiohttp.ClientSession() as session:
            url = "https://api.vk.com/method/groups.getLongPollServer"
            params = LpParamsLinkRequest(
                access_token=config.VK_TOKEN.get_secret_value(),
                group_id=config.GROUP_ID.get_secret_value()
            )
            async with session.get(url, params=asdict(params)) as response:
                data = await response.json()
                return ServerParams.from_raw_data(data['response'])

    async def _network_watcher(self, check_interval: float = 2.0) -> None:
        while not self._stop_event.is_set():
            if self.vpn_monitor.has_state_changed():
                self.inform.emit(f"[{self.name}] Обнаружено переключение впн. Пересоздаю сессию...")
                self._restart_event.set()
                try:
                    await self.session_manager.recreate_session()
                except Exception as e:
                    self.error.emit(f"[{self.name}] Ошибка пересоздания сессии")
                finally:
                    self._restart_event.clear()

            await asyncio.sleep(check_interval)

    async def _try_longpoll(self, server_params: ServerParams) -> None:
        """ Основная бизнес-логика над циклом long-poll запроса с обработкой ошибок"""
        try:

            raw_updates = await self._longpoll_sequence(server_params)
            if raw_updates is None:
                return

            update_list = self._parse_updates(raw_updates)
            if update_list is None:
                return

            self._handle_updates(update_list, server_params)
        except asyncio.CancelledError:
            self.inform.emit(f"[{self.name}] Получен сигнал  отключения Long-poll. Выключение...")
            raise
        except aiohttp.ClientError as e:
            await self._handle_aio_client_error(e)
        except RuntimeError as re:
            if "Session is closed" in str(re):
                self.inform.emit(f"[{self.name}] Запрос прерван. Перезапуск запроса.")
                await asyncio.sleep(3)
            else:
                raise
        except Exception as e:
            self.error.emit(f"[{self.name}] Ошибка в работе Long-poll цикла. Свяжитесь с разработчиком.{e}")
            await asyncio.sleep(5)

    def _parse_updates(self, raw_updates: dict) -> Updates | None:
        """ Метод обработки пришедшего события """
        try:
            return Updates.from_raw_data(raw_updates)
        except TypeError as te:
            self.error.emit(f"[{self.name}] Type error. Не удалось распарсить значения. {te}")
            return None
        except Exception as e:
            self.error.emit(f"[{self.name}] Не удалось распарсить ответ от вк! Необходима проверка DC {e}")
            return None

    def _handle_updates(self, update_list: Updates, server_params: ServerParams) -> None:
        """ Обработка полученных событий """
        if update_list.failed == 1:
            self.warning.emit(
                f"[{self.name}] Внимание! Некорректный ответ при long-poll запросе + LOG")
            self.logger.debug(update_list)
            return

        server_params.ts = update_list.ts
        for update in update_list.updates:
            self.queue.put(update)

    async def _handle_aio_client_error(self, e):
        """ Логика обработки ошибок от вк """
        if "Connection timeout to host" in str(e):
            self.warning.emit(f"[{self.name}] Вынужденная задержка перед переотправкой запроса 5 секунд.")
            await asyncio.sleep(5)
        else:
            # На случай фатальной ошибки сессии
            self.error.emit(f"[{self.name}] Фатальная ошибка Long-poll цикла. Свяжитесь с разработчиком. {e}")
            await self.session_manager.recreate_session()
            await asyncio.sleep(5)


@dataclass(frozen=True)
class LpParamsLinkRequest:
    access_token: str
    v: str = "5.199"
    group_id: str | None = None


@dataclass()  # ts будет меняться в процессе, поэтому параметр frozen не установлен
class ServerParams:
    server: str
    key: str
    ts: str

    @classmethod
    def from_raw_data(cls, data: dict) -> ServerParams:
        return cls(
            server=data['server'],
            key=data['key'],
            ts=data['ts']
        )

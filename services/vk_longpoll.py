from __future__ import annotations  # Postponed annotation calculation

import asyncio
from dataclasses import dataclass, asdict
from queue import Queue

import aiohttp

from config.config_reader import config
from config.logger_settings import get_logger
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
        self.inform.emit(f"Инициализация {self.name}")
        self._session = None
        self.queue = event_queue

    async def _main_loop(self) -> None:
        """ Запуск цикла получения событий """
        if self._session is not None:
            if not self._session.closed:
                self.inform.emit(f"{self.name}: закрытие старой сессии")
                await self._session.close()
            self._session = None
            self.logger.debug(f"{self.name}: состояние сессии сброшено")

        self.inform.emit(f"Запускаю {self.name}...")
        self._stop_event.clear()
        await self._longpoll_cycle()

    async def _longpoll_cycle(self) -> None:
        """ Основой цикл опроса вк """
        server_params = await self._get_long_poll_params()
        self._session = aiohttp.ClientSession()
        # Внешний try для корректного закрытия сессии aiohttp
        try:
            while not self._stop_event.is_set():
                try:
                    raw_updates = await self._longpoll_sequence(server_params)
                    try:
                        update_list = Updates.from_raw_data(raw_updates)
                    except TypeError as te:
                        self.error.emit(f"[{self.name}] Type error. Не удалось распарсить значения.")
                        self.logger.error(f"Type error. Не удалось распарсить значения: {te}")
                    except Exception as e:
                        self.error.emit(f"[{self.name}] Не удалось распарсить ответ от вк! Необходима проверка DC")
                        self.logger.error(f"Ошибка парсинга. Необходима проверка корректности датакласса!!! {e}")
                        break

                    if update_list:
                        server_params.ts = update_list.ts
                        for update in update_list.updates:
                            self.queue.put(update)
                except asyncio.CancelledError:
                    self.inform.emit(f"[{self.name}] Получен сигнал  отключения Long-poll. Выключение...")
                    raise
                except aiohttp.ClientError as e:
                    # На случай фатальной ошибки сессии
                    self.error.emit(f"[{self.name}] Фатальная ошибка Long-poll цикла. Свяжитесь с разработчиком.")
                    self.logger.error(f"Фатальная ошибка Long-poll цикла: {e}")
                    await self._session.close()
                    self._session = aiohttp.ClientSession()
                    await asyncio.sleep(5)
                except Exception as e:
                    self.error.emit(f"[{self.name}] Ошибка в работе Long-poll цикла. Свяжитесь с разработчиком.")
                    self.logger.error(f"Ошибка в работе Long-poll цикла: {e}")
                    await asyncio.sleep(5)
        finally:
            await self._session.close()

    async def _longpoll_sequence(self,
                                 server_params: ServerParams,
                                 wait: int = 25) -> dict | None:
        """ Метод единичного запроса событий (long-poll) """
        url = f"{server_params.server}?act=a_check&key={server_params.key}&ts={server_params.ts}&wait={wait}"
        async with self._session.get(url) as response:
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

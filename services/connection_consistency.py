import asyncio
import platform
import subprocess

import aiogram
import aiohttp


class NetworkMonitor:
    """ Класс анализатор состояния сети """

    def __init__(self):
        self.system = platform.system()
        self._vpn_state: bool = False

    def get_routes(self) -> list[str]:
        """
        Функция-распределитель.
        Выбирает метод сбора информации относительно системы.
        :return Список gateway
        """
        if self.system == "Darwin":
            return self._get_routes_macos()
        if self.system == "Windows":
            return self._get_routes_win()
        if self.system == "Linux":  # TODO: ENUM
            raise OSError("Внимание! Проверка VPN не реализована для Linux-платформы.")
        raise OSError("Внимание! Непредусмотренный тип системы! Проверка VPN не будет работать!")

    def _get_routes_win(self) -> list[str]:
        """ Функция для Windows """
        result = subprocess.run(
            ['route', 'print', '0.0.0.0'],
            capture_output=True, text=True, timeout=3
        )
        routes = []
        for line in result.stdout.split('\n'):
            if line.strip().startswith('0.0.0.0'):
                parts = line.split()
                if len(parts) >= 5:
                    routes.append(parts[2])  # Добавляем только gateway
        return routes

    def _get_routes_macos(self) -> list[str]:
        """ Функция для MAC """
        result = subprocess.run(
            ['netstat', '-rn'],
            capture_output=True, text=True, timeout=3
        )
        routes = []
        for line in result.stdout.split('\n'):
            if line.startswith('default'):
                parts = line.split()
                if len(parts) >= 6:
                    routes.append(parts[1])  # Добавляем только gateway
        return routes

    def is_vpn(self, routes: list[str]) -> bool:
        """ Функция проверки gateway на наличие определённых частей """
        for route in routes:
            if route.startswith( #TODO: Вынести адреса в настройки
                    ('10.', '172.16.', '172.17.',
                     '172.18.', '172.19.', '172.20.',
                     '172.21.', '172.22.', '172.23.',
                     '172.24.', '172.25.', '172.26.',
                     '172.27.', '172.28.', '172.29.',
                     '172.30.', '172.31.')
            ):
                return True
        return False

    def has_state_changed(self) -> bool:
        """ Метод для проверки изменения состояния сети """
        routes = self.get_routes()
        current = self.is_vpn(routes)
        if current != self._vpn_state:
            self._vpn_state = current
            return True
        else:
            return False


class ReSession:
    """
    Класс для создания настраиваемой сессии aiohttp
    с вспомогательными методами для перезапуска
    и взаимодействия с монитором состояния сети
    """

    def __init__(self, monitor: NetworkMonitor) -> None:
        self.monitor = monitor
        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._aiogram_bot: aiogram.Bot | None = None
        self._lock = asyncio.Lock() # Если будет несколько точек обращения к сессии
        self._closed = False

    async def _create_session(self) -> aiohttp.ClientSession:
        """ Функция, создающая сессию aiohttp """
        timeout = aiohttp.ClientTimeout(
            total=40,
            connect=5,
            sock_read=25,
        )

        return aiohttp.ClientSession(timeout=timeout)

    async def _create_bot(self) -> aiogram.Bot:
        """ Функция создания бота для aiogram3 """
        # TODO: Реализация, если будет сильная нагрузка. На текущий момент решено bot.close() после каждого запроса
        pass

    async def get_session(self) -> aiohttp.ClientSession:
        """ Функция контроля сессии в asyncio """
        async with self._lock:
            if self._aiohttp_session is None or self._aiohttp_session.closed:
                self._aiohttp_session = await self._create_session()
            return self._aiohttp_session

    async def recreate_session(self) -> None:
        """ Функция пересоздания сессии """
        async with self._lock:
            if self._aiohttp_session and not self._aiohttp_session.closed:
                await self._aiohttp_session.close()
                await asyncio.sleep(0.5)
            self._aiohttp_session = await self._create_session()

    async def close(self) -> None:
        """ Функция закрытия сессии """
        self._closed = True
        if self._aiohttp_session and not self._aiohttp_session.closed:
            await self._aiohttp_session.close()

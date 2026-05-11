import asyncio
import queue
from queue import Queue

from aiogram import types
from aiogram.exceptions import TelegramBadRequest

from config.logger_settings import get_logger
from model.vk_response_dcs import UpdateUnit
from services.tg_session import TgTransport
from .gui.gui_support import AsyncPyQtWorker


class UpdateProcessor(AsyncPyQtWorker):
    """
    Асинхронный класс-consumer событий от вк. Получает их из очереди
    """

    def __init__(self, event_queue: Queue) -> None:
        super().__init__("UpdateProcessor")
        self.logger = get_logger(self.name)  # "UpdateProcessor"
        self.queue = event_queue

        # self.tg_transport нельзя создавать здесь, иначе объект будет привязан к первому Event-loop
        # и при перезапуске будет давать ошибку, что event-loop уже закрыт
        self.tg_transport: TgTransport = None

    async def _main_loop(self) -> None:
        """ Запуск главного цикла обработки событий от вк """
        self.inform.emit(f"[{self.name}] Запуск обработчика задач...")
        self.tg_transport = TgTransport()
        while not self._stop_event.is_set():
            try:
                try:
                    raw_update: UpdateUnit = await self._get_updates_from_queue(timeout=5)
                except asyncio.TimeoutError:
                    continue

                if raw_update is None:
                    continue

                await self._tg_transport_try(raw_update)

            except Exception as e:
                self.error.emit(f"[{self.name}] Произошла ошибка во время обработки события от вк")
                self.logger.error(f"Ошибка обработки задачи: {e}")
                # Не убиваем процесс при ошибке + короткая задержка перед продолжением обработки
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

    async def _tg_transport_try(self, update: UpdateUnit):
        """ Метод взаимодействия с тг транспортом. Вынесен для корректной обработки ошибок """
        try:
            if update.object.attachments:
                response_task = self._process(update)
                await self.tg_transport.send_w_media(response_task)
            else:
                response_task = self._append_prefix(update.object.text)
                await self.tg_transport.send_wo_media(response_task)
        except TelegramBadRequest as tge:
            self.error.emit(f"Произошла ошибка Telegram: {tge}")
        except Exception as e:
            self.error.emit(f'Непредвиденная ошибка при отправке сообщения в Telegram: {e}')

    async def _get_updates_from_queue(self, timeout: float) -> UpdateUnit | None:
        """ Асинхронное получение события из синхронной очереди с таймаутом """
        deadline = asyncio.get_event_loop().time() + timeout

        while not self._stop_event.is_set():
            try:
                return self.queue.get_nowait()
            except queue.Empty:
                if asyncio.get_event_loop().time() >= deadline:
                    raise asyncio.TimeoutError()

                await asyncio.sleep(0.1)

        return None

    def _process(self, raw_update: UpdateUnit) -> list[types.InputMediaPhoto] | Exception:
        """
        Обработка события - вызов транспорта до тг
        :param raw_update: Сырые данные о событии, полученные от вк (только с прикреплёнными файлами)
        :return: список элементов для отправки через aiogram (types.InputMediaPhoto)
        """
        attachment_list = []
        if raw_update.object.attachments:
            for i, attachment in enumerate(raw_update.object.attachments):
                photo_url = attachment.photo.orig_photo.url
                if i == 0:
                    attachment_list.append(types.InputMediaPhoto(
                        media=photo_url,
                        caption=self._append_prefix(raw_update.object.text)
                    ))
                else:
                    attachment_list.append(types.InputMediaPhoto(
                        media=photo_url
                    ))
            return attachment_list
        else:
            raise Exception("Пустой список прикреплённых файлов!")

    def _append_prefix(self, update_text: str) -> str:
        """ Добавляет *настраиваемый* префикс к пересылаемым сообщениям """
        # TODO insert proper link
        return f'Заказать ? t.me/ \n {update_text}'

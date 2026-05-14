import asyncio
import queue
import re
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
    _VK_LINK_RE_PATTERN = re.compile(r'([^\[]*)\[#alias\|[^|]*\|([^]]*)](.*)')

    _LINK_RE_PATTERN = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')

    def __init__(self, event_queue: Queue) -> None:
        super().__init__("UpdateProcessor")
        self.logger = get_logger(self.name)  # "UpdateProcessor"
        self.queue = event_queue

        self.text_processors = [
            ('LINK_PROCESS', self._sort_links),
            ('APPEND_PREFIX', self._append_prefix),
            ('TRIM_LINKS', self._trim_links),
        ]
        
        # self.tg_transport нельзя создавать здесь, иначе объект будет привязан к первому Event-loop
        # и при перезапуске будет давать ошибку, что event-loop уже закрыт
        self.tg_transport: TgTransport = None

    async def _main_loop(self) -> None:
        """ Запуск главного цикла обработки событий от вк """
        self.inform.emit(f"[{self.name}] Запуск обработчика задач...")
        self.tg_transport = TgTransport()
        self._stop_event = asyncio.Event()

        while not self._stop_event.is_set():
            try:
                try:
                    raw_update: UpdateUnit | None = await self._get_updates_from_queue(timeout=5)
                except asyncio.TimeoutError:
                    continue

                if raw_update is None:
                    continue

                await self._tg_transport_try(raw_update)

            except Exception as e:
                self.error.emit(f"[{self.name}] Произошла ошибка во время обработки события от вк")
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
            await self._do_tg_send(update)
        except TelegramBadRequest as tge:
            self.error.emit(f"[{self.name}] Произошла ошибка Telegram: {tge}")
        except Exception as e:
            if "Flood control exceeded" in str(e):
                self.error.emit(f"[{self.name}] Превышение лимита на отправку сообщений в ТГ. Ожидание 60 секунд.")
                await asyncio.sleep(60)
                await self._do_tg_send(update)
                return
            self.error.emit(f'[{self.name}] Непредвиденная ошибка при отправке сообщения в Telegram: {e}')

    async def _do_tg_send(self, update: UpdateUnit):
        """ Непосредственная отправка. Вынесена для логики переотправки """
        if len(update.object.attachments) > 0 and update.object.attachments[0].type != 'link':  # TODO TYPES_ENUM
            response_task = self._process(update)
            await self.tg_transport.send_w_media(response_task)
        else:
            response_task = self._process_text(update.object.text)
            await self.tg_transport.send_wo_media(response_task)

    async def _get_updates_from_queue(self, timeout: float) -> UpdateUnit | None:
        """ Асинхронное получение события из синхронной очереди с таймаутом """
        deadline = asyncio.get_event_loop().time() + timeout

        while not self._stop_event.is_set():
            try:
                return self.queue.get_nowait()
            except queue.Empty:
                if asyncio.get_event_loop().time() >= deadline:
                    raise asyncio.TimeoutError()

                await asyncio.sleep(3)

        return None

    def _process(self, raw_update: UpdateUnit) -> list[types.InputMediaPhoto] | Exception:
        """
        Обработка события - вызов транспорта до тг.
        :param raw_update: Сырые данные о событии, полученные от вк (только с прикреплёнными файлами)
        :return: список элементов для отправки через aiogram (types.InputMediaPhoto)
        """
        attachment_list = []
        if processed_text := raw_update.object.text:
            processed_text = self._process_text(processed_text)
        if raw_update.object.attachments:
            for i, attachment in enumerate(raw_update.object.attachments):
                photo_url = attachment.photo.orig_photo.url
                if i == 0:
                    attachment_list.append(types.InputMediaPhoto(
                        media=photo_url,
                        caption=processed_text
                    ))
                else:
                    attachment_list.append(types.InputMediaPhoto(
                        media=photo_url
                    ))
            return attachment_list
        else:
            raise Exception("Пустой список прикреплённых файлов!")

    def _process_text(self, text: str) -> str:
        """
        Метод-итератор по правилам обработки текста сообщения.
        :return Обработанный текст или исходный текст в случае ошибки.
        """
        before_update = text

        for processor_name, processor_func in self.text_processors:
            try:
                text = processor_func(text)
            except Exception as e:
                self.error.emit(f"[{self.name}] Произошла ошибка во время обработки текста на этапе {processor_name}")
                self.error.emit(f"[{self.name}] Сообщение ошибки: {e}")
                self.error.emit(f"[{self.name}] Сообщение будет отправлено без обработки")
                return before_update
        return text

    def _append_prefix(self, update_text: str) -> str:
        """ Добавляет *настраиваемый* префикс к пересылаемым сообщениям """
        # TODO insert proper link
        return f'Заказать ? t.me/ \n{update_text}'

    def _sort_links(self, unprocessed_text: str) -> str:
        """ Чистит ссылки в тексте от плейсхолдеров, автоматически устанавливаемых ВК """
        return self._VK_LINK_RE_PATTERN.sub(r'\1\2\3', unprocessed_text)

    def _trim_links(self, unprocessed_text: str) -> str:
        """ Вырезает ссылки, если выходим за 4000 символов """
        # TODO: Нарезка на несколько сообщений?
        if len(unprocessed_text) > 1000:
            self.warning.emit(f"[{self.name}] Слишком длинное сообщение. Пробую удалить ссылки. Ссылки будут сохранены в файлах лога")
            processed = re.sub(self._LINK_RE_PATTERN, "", unprocessed_text)
            if len(processed) > 1000:
                self.error.emit(f"[{self.name}] Чересчур длинное сообщение! Пожалуйста, отправьте самостоятельно!")
            for num, link in enumerate(re.findall(self._LINK_RE_PATTERN, unprocessed_text)):
                self.logger.warning(f"[{num}] {link}")
            return processed
        return unprocessed_text


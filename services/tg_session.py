from aiogram import Bot, types
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from config.config_reader import config


class TgTransport:
    """ Транспортный класс для отправки сообщений в телеграм """

    def __init__(self):
        """ Инициализация бота для телеграм """
        self.bot = Bot(
            token=config.TG_TOKEN.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.CHANNEL_ID = config.CHANNEL_ID.get_secret_value()
        self.MSG_THREAD = config.MSG_THREAD.get_secret_value()

    async def send_wo_media(self, message: str) -> None:
        """ Отправка текстового сообщения в Телеграм """
        # TODO обработка ответа? Хранение времени последней отправки?
        response = await self.bot.send_message(
            chat_id=self.CHANNEL_ID,
            message_thread_id=self.MSG_THREAD,
            text=message
        )
        # TODO: При большой нагрузке убрать постоянное закрытие сессии
        #  и реализовать перезапуск сессии при подозрении на включённый впн
        #  или установить ttl_dns_cache на ~10 секунд при создании сессии
        await self.bot.session.close()

    async def send_w_media(self, payload: list[types.InputMediaPhoto]) -> None:
        """ Отправка сообщения с прикреплёнными фотографиями в Телеграм """
        # TODO обработка ответа?
        response = await self.bot.send_media_group(
            chat_id=self.CHANNEL_ID,
            media=payload,
            message_thread_id=self.MSG_THREAD
        )
        # TODO: При большой нагрузке убрать постоянное закрытие сессии
        #  и реализовать перезапуск сессии при подозрении на включённый впн
        #  или установить ttl_dns_cache на ~10 секунд при создании сессии
        await self.bot.session.close()

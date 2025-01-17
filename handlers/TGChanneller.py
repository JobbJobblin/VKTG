import asyncio
import logging
from aiogram import Bot, types
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

async def Channelling(PHOTO_URLS: list, caption: str = None):
    """Отправляет медиагруппу в Telegram."""

    from config_reader import config
    bot = Bot(token=config.TG_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    CHANNEL_ID = config.CHANNEL_ID.get_secret_value()
    MSG_THREAD = config.MSG_THREAD.get_secret_value()

    caption = f'Заказать 👉 t.me/yulia_mybestsale \n {caption}'

    print(PHOTO_URLS)
    if PHOTO_URLS:
        print(1)
        try:
            media_group = []
            for i, url in enumerate(PHOTO_URLS):
                # Добавляем подпись только к первому фото
                if i == 0 and caption:
                    media_group.append(types.InputMediaPhoto(media=url, caption=caption))
                else:
                    media_group.append(types.InputMediaPhoto(media=url))

            if media_group:
                await bot.send_media_group(chat_id=CHANNEL_ID, media=media_group, message_thread_id=MSG_THREAD)
            else:
                print("Нет фото для отправки.")

        except TelegramBadRequest as e:
            logging.error(f"Ошибка при отправке фотографий: {e}")
            print(f"Произошла ошибка при отправке фотографий. Подробности в логах.")
        except Exception as e:
            logging.error(f"Непредвиденная ошибка: {e}")
            print(f"Произошла непредвиденная ошибка. Подробности в логах.")

    else:
        await bot.send_message(chat_id = CHANNEL_ID, message_thread_id = MSG_THREAD, text = caption)



    await bot.session.close()
    PHOTO_URLS.clear()
    return print('Post is sent')


if __name__ == '__main__':
    PHOTO_URLS = [
        "https://sun9-80.userapi.com/s/v1/ig2/ZTuRQrwqj8Sr05UDt1rZBU6YOKPVOsauhZu6s35UO50tPmE4AkKqUBeNdxTyxtRgLOntyJt_ekiUNxkNc_YuvAeZ.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,500x500&from=bu&u=VxK2ZxUfmy6cQLXL4VflyOVYEQ7M0RV7mJ0xIjEBe0g",
        "https://sun9-80.userapi.com/s/v1/ig2/ZTuRQrwqj8Sr05UDt1rZBU6YOKPVOsauhZu6s35UO50tPmE4AkKqUBeNdxTyxtRgLOntyJt_ekiUNxkNc_YuvAeZ.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,500x500&from=bu&u=VxK2ZxUfmy6cQLXL4VflyOVYEQ7M0RV7mJ0xIjEBe0g",
        "https://sun9-80.userapi.com/s/v1/ig2/ZTuRQrwqj8Sr05UDt1rZBU6YOKPVOsauhZu6s35UO50tPmE4AkKqUBeNdxTyxtRgLOntyJt_ekiUNxkNc_YuvAeZ.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,500x500&from=bu&u=VxK2ZxUfmy6cQLXL4VflyOVYEQ7M0RV7mJ0xIjEBe0g"
    ]

    asyncio.run(Channelling(PHOTO_URLS, caption='Говно с дымом!'))

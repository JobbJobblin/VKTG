import asyncio
import aiohttp
from aiogram import Bot, types

# Замените на свой токен
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Пути к файлам
PHOTO_LINKS_FILE = "photo_links.txt"
TEXT_FILE = "post_text.txt"


async def send_post(bot: Bot, chat_id: int, photo_links: list, text: str):
    """Отправляет пост с фотографиями в Telegram."""
    try:
        media = []
        for link in photo_links:
            async with aiohttp.ClientSession() as session:
                async with session.get(link) as resp:
                    if resp.status == 200:
                        photo = await resp.read()
                        media.append(types.InputFile(photo))
                    else:
                        print(f"Ошибка загрузки фотографии по ссылке {link}: статус {resp.status}")
                        #Можно добавить логику для пропуска фото, если не удалось загрузить
                        continue # Пропускаем фото, если загрузка не удалась

        if media: #Проверка на наличие загруженных фото
            await bot.send_media_group(chat_id, media=media)
        else:
            print("Не удалось загрузить ни одной фотографии.")


        if text:
            await bot.send_message(chat_id, text)
    except aiohttp.ClientError as e:
        print(f"Ошибка при обращении к одной из ссылок: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка при отправке поста: {e}")



async def main():
    """Основная функция."""
    bot = Bot(token=BOT_TOKEN)
    try:
        with open(PHOTO_LINKS_FILE, "r") as f:
            photo_links = [line.strip() for line in f]
        with open(TEXT_FILE, "r", encoding="utf-8") as f: #Добавлена кодировка utf-8
            text = f.read()
    except FileNotFoundError:
        print(f"Один или оба файла ({PHOTO_LINKS_FILE}, {TEXT_FILE}) не найдены.")
        return

    await send_post(bot, chat_id=YOUR_CHAT_ID, photo_links=photo_links, text=text) # Замените YOUR_CHAT_ID на ID чата
    await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
# VKTG 📢

**VKTG** — это проект, который позволяет автоматически публиковать посты из группы Вконтакте в канал Telegram. Проект использует API ВКонтакте и Telegram для синхронизации контента между платформами.

## 📌 Оглавление

- [Установка](#установка)
- [Настройка](#настройка)
- [Использование](#использование)
- [Как внести вклад](#как-внести-вклад)
- [Лицензия](#лицензия)
- [Контакты](#контакты)

## 🛠️ Установка

Для начала работы с проектом, склонируйте репозиторий и установите необходимые зависимости.

```bash
# Клонирование репозитория
git clone https://github.com/JobbJobblin/VKTG.git
cd VKTG

# Установка зависимостей
pip install -r requirements.txt
```
## ⚙️ Настройка
Получение токенов доступа:

ВКонтакте: Перейдите по [ссылке](https://dev.vk.com/ru/?ref=old_portal) и создайте новое приложение. Получите токен доступа с правами wall, groups, и photos.

Telegram: Создайте бота через BotFather и получите токен.

Настройка конфигурации:

Создайте файл .env в корневой директории проекта.

Добавьте в него следующий код:

VK_TOKEN = 'ваш_токен_доступа_vk'  
GROUP_ID_MINUS = 'Ваш id группы vk с минусом'  
GROUP_ID = 'Ваш id группы vk'  
TG_TOKEN = 'ваш_токен_бота_telegram'  
CHANNEL_ID = 'Ваш id канала tg с минусом'  
MSG_THREAD = 'Номер тематической подгруппы'  

## 🚀 Использование
После настройки, запустите скрипт для синхронизации постов.

bash
Copy
python main.py
Скрипт будет автоматически проверять новые посты в указанном Telegram-канале и публиковать их в вашу группу ВКонтакте.

## 📄 Лицензия
Этот проект распространяется под лицензией MIT.

## 📬 Контакты
Если у вас есть вопросы или предложения, пожалуйста, свяжитесь со мной:

GitHub: [JobbJobblin](https://github.com/JobbJobblin)

Email: JobbJobblin@gmail.com  
Telegram: @SImonFry

Спасибо за внимание! Надеюсь, этот проект будет полезен для вас. 😊

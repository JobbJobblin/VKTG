import vk_api
import asyncio
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from handlers.TGChanneller import Channelling

def VkPars():
    from config_reader import config #Импорт токеов и пр
    vk_session = vk_api.VkApi(token=config.VK_TOKEN.get_secret_value())
    GROUP_ID_MINUS= config.GROUP_ID_MINUS.get_secret_value() #Нужен ID группы именно с минусом
    GROUP_ID = config.GROUP_ID.get_secret_value()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    vk = vk_session.get_api()
    print('Смотрю на вашу стену.') #Оповещение пользователя
    Photo_Url_List = []

    try:
        for event in longpoll.listen():
            if event.type == VkBotEventType.WALL_POST_NEW:

                Post_info = vk.wall.get(domain=GROUP_ID_MINUS, count=2) #Берём последние два поста на стене, чтобы избежать закреплённого
                if 'is_pinned' not in Post_info['items'][0]: #Проверка на закреплённый пост
                    if 'attachments' in Post_info['items'][0]: #Проверка на наличие прикреплённых объектов
                        for attachment in Post_info['items'][0]['attachments']:
                            if attachment['type'] == 'photo': #Проверка на тип объекта - фотографии
                                Photo_url = attachment['photo']['orig_photo']['url'] #Берём url оригинального размера фото
                                Photo_Url_List.append(Photo_url) #Добавляем url фотографий в список
                    if Post_info['items'][0]:
                        Post_Text = str(Post_info['items'][0]['text'])
                        print(Post_Text)
                else:
                    print(f"Есть закреплённый пост - is pinned = {Post_info['items'][0]['is_pinned']}")
                    if 'attachments' in Post_info['items'][1]: # Проверяем на наличие прикреплённых объектов. Используем 1, а не 0 (второй пост, не первый) из-за закреплённого поста
                        for attachment in Post_info['items'][1]['attachments']:
                            if attachment['type'] == 'photo': #Проверка на тип объекта - фотографии
                                Photo_url = attachment['photo']['orig_photo']['url'] #Берём url оригинального размера фото
                                Photo_Url_List.append(Photo_url) #Добавляем url фотографий в список
                    if Post_info['items'][1]:
                        Post_Text = str(Post_info['items'][1]['text'])
                        print(Post_Text)
            print ('Новый пост!')
            asyncio.run(Channelling(PHOTO_URLS = Photo_Url_List, caption = Post_Text))


    except Exception as e:
        print(f'Что-то пошло не так: {e}')
    finally:
        print('Завершение работы...')

if __name__ == '__main__':
    VKP = VkPars()
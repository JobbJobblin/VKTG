from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse, parse_qs
import time

@DeprecationWarning
def get_kate_mobile_token():
    """
    Получает access_token через официальное приложение Kate Mobile,
    дожидаясь редиректа на oauth.vk.com/blank.html.
    """
    # Параметры Kate Mobile
    client_id = "2685278"
    scope = "wall,groups,offline"
    redirect_uri = "https://oauth.vk.com/blank.html"
    v_api = "5.199"

    # Формируем URL для Implicit Flow
    auth_url = (
        f"https://oauth.vk.com/authorize?"
        f"client_id={client_id}&"
        f"display=page&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}&"
        f"response_type=token&"
        f"v={v_api}"
    )

    # Запускаем браузер
    driver = webdriver.Chrome()  # Убедитесь, что chromedriver в PATH, или укажите путь
    driver.get(auth_url)

    print("Пожалуйста, войдите в аккаунт ВКонтакте в открывшемся окне...")
    print("Ожидание редиректа на страницу с токеном...")

    try:
        # Ждем, пока URL не будет содержать 'access_token' И мы не окажемся на blank.html
        # Даем 2 минуты на вход и подтверждение прав
        WebDriverWait(driver, 120).until(
            lambda d: 'access_token' in d.current_url and 'oauth.vk.com/blank.html' in d.current_url
        )

        # Извлекаем URL-фрагмент с токеном
        final_url = driver.current_url
        print(f"Обнаружен редирект: {final_url[:70]}...")

        fragment = urlparse(final_url).fragment
        params = parse_qs(fragment)
        token = params.get('access_token', [None])[0]
        user_id = params.get('user_id', [None])[0]

        if token:
            print(f"✅ Токен успешно получен!")
            print(f"👤 ID пользователя: {user_id}")
            print(f"🔑 Токен: {token}")
            return token
        else:
            print("❌ Токен не найден во фрагменте URL.")
            return None

    except TimeoutException:
        print("⏰ Время ожидания истекло. Вы не успели войти или не нажали 'Разрешить'.")
        return None
    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        return None
    finally:
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    get_kate_mobile_token()
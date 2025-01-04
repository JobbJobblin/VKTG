import threading
import logging
import sys

from handlers.VKParse import VkPars

stop_event = threading.Event()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout
)

def check_input():
    input('Нажмите Enter, чтобы остановить безумие \n')
    stop_event.set()

if __name__ == '__main__':
    vk_thread = threading.Thread(target=VkPars)
    vk_thread.daemon = True
    vk_thread.start()

    input_thread = threading.Thread(target=check_input)
    input_thread.start()

    input_thread.join()
    print('Программа остановлена')
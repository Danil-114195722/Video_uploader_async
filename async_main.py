#!./venv/bin/python


import re
import os
from time import time

import asyncio
import aiohttp

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class DontWantClearDir(Exception):
    pass


class NothingFound(Exception):
    pass


async def uploader(link, num, path, underscore_query):
    user_agent = UserAgent()

    # делаем запрос на страницу с одним видео
    try:
        response_video = requests.get(link, headers={'User-Agent': user_agent.random}, timeout=2)
        # читаем и загружаем видео
        with open(f'{path}/{underscore_query}_{num}.mp4', 'wb') as video:
            for chunk in response_video.iter_content(1024 * 200):
                video.write(chunk)
            print(f'File number {num} have uploaded!')

    except asyncio.exceptions.TimeoutError:
        print(f'File number {num} corrupted :(')


# скачиваем указанное кол-во видео по данному запросу
async def main(query, amount, check_empty_files=True):
    user_agent = UserAgent()

    default_url = 'https://www.istockphoto.com/ru/search/2/film'
    slug_query = re.sub('\s', '%20', query)

    # список задач
    tasks = []

    # здесь будут храниться ссылки на все видео
    all_links = []

    async with aiohttp.ClientSession() as session:
        try:
            count = 0
            page = 1

            while count < amount:
                # передаём в поиск запрос и номер страницы
                params = {
                    'phrase': slug_query,
                    'page': page
                }
                async with session.get(default_url, headers={'User-Agent': user_agent.random}, params=params, timeout=2) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    page_links = [re.sub('&amp;', '&', figure.find('video')['src']) for figure in soup.findAll('figure', limit=amount - count)]

                    # если страница первая, то парсим запрос со страницы (есть автозамена)
                    if page == 1:
                        real_query = soup.find('input', {'name': 'phrase'})['value']

                    # если страницы не существует
                    if not page_links:
                        break

                    all_links += page_links
                    count += len(page_links)
                    page += 1

            # если ссылок на видео не найдено
            if len(all_links) == 0:
                raise NothingFound

            # путь к директории
            underscore_query = re.sub('\s', '_', real_query)
            path = f'./async_all_videos/catalog_{underscore_query}_videos'

            # создаём директорию
            try:
                os.mkdir(path)
            # если такая директория существует, то чистим её (предварительно спросив у пользователя)
            except OSError:
                print('Do you agree that I can clear this directory? [y, n]', end=' ')
                while True:
                    answer = input()
                    if answer in ['y', 'д']:
                        for file in os.listdir(path):
                            os.remove(f'{path}/{file}')
                        break
                    elif answer in ['n', 'н']:
                        raise DontWantClearDir
                    else:
                        print('Wrong parameters have been entered! Try again [y, n]', end=' ')

            for num, link in enumerate(all_links, 1):
                task = asyncio.create_task(uploader(link, num, path, underscore_query))
                tasks.append(task)
            await asyncio.gather(*tasks)

            # если файлы скачивались
            try:
                if check_empty_files:
                    # удаляем пустые файлы
                    for file in os.listdir(path):
                        path_file = f'{path}/{file}'
                        # если размер файла - 0 байт
                        if os.stat(path_file).st_size == 0:
                            os.remove(path_file)
                            print(f'File "{file}" has been deleted, because it was empty :(')

                print(f"\nThere are all the videos I could find and upload for your request: {str(len(os.listdir(path)))}")
                print(f'{str(round(start - time(), 2))} seconds have passed')
            # если по запросу ничего не найдено, то ничего не делаем
            except FileNotFoundError:
                pass

        except NothingFound:
            print('Nothing found!\nCheck your request!')
        except DontWantClearDir:
            print("Videos haven't been uploaded!")
        except asyncio.exceptions.TimeoutError:
            print("I'm sorry, try again...")
        except Exception as error:
            print(f'Ha-ha-ha, you caught the error in "Video_uploader", in "async_main.py", in func "main": {error}')


if __name__ == '__main__':
    while True:
        # это если пользователь решит ввести вместо числа строку
        try:
            query = input('Enter query: ').lower()
            amount = int(input('Enter desired amount: '))

            start = time()
            asyncio.run(main(query, amount))

            break
        # при ошибке выводим сообщение
        except Exception:
            print('\nWrong parameters have been entered!\nCheck your request and try again!\n')

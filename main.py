#!./venv/bin/python


import re
import os
from time import time

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


# скачиваем указанное кол-во видео по данному запросу
def downloader_videos(query, amount) -> None:
    user_agent = UserAgent()

    slug_query = re.sub('\s', '%20', query)
    # начальная страница
    default_url = 'https://www.istockphoto.com/ru/search/2/film'

    # здесь будут храниться ссылки на все видео
    all_links = []
    count = 0
    page = 1

    while count < amount:
        # передаём в поиск запрос и номер страницы
        params = {
            'phrase': slug_query,
            'page': page
        }
        try:
            res = requests.get(default_url, headers={'User-Agent': user_agent.random}, params=params, timeout=5)
            html = res.text
        except Exception as error:
            print('Sorry, we have little server problems, but we will fix it soon...')
            print(f'Ha-ha-ha, you got the error: {error}')
            return

        soup = BeautifulSoup(html, 'lxml')
        page_links = [re.sub('&amp;', '&', figure.find('video')['src']) for figure in soup.findAll('figure', limit=amount-count)]

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
        print('Page not found...\nCheck your request!')
        return

    # создаём директорию
    underscore_query = re.sub('\s', '_', real_query)
    path = f'./all_videos/catalog_{underscore_query}_videos'
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
                print("Videos haven't been downloaded")
                return
            else:
                print('Wrong parameters have been entered! Try again [y, n]', end=' ')

    # по всем ссылкам качаем видео
    for num, link in enumerate(all_links, 1):
        # делаем запрос на страницу с одним видео
        try:
            res_from_video = requests.get(link, headers={'User-Agent': user_agent.random}, timeout=5, stream=True)
        except Exception:
            break

        # побитно записываем файл
        with open(f'{path}/{real_query}_{num}.mp4', 'wb') as video:
            for chunk in res_from_video.iter_content(1024 * 200):
                video.write(chunk)
                print('.', end='')
        print('Done!')

    try:
        print(f"\nThere are all the videos I could find and upload for your request: {str(len(os.listdir(path)))}")
        print(f'{str(round(start - time(), 2))} seconds have passed')
    except FileNotFoundError:
        pass

if __name__ == '__main__':
    # это если пользователь решит ввести вместо числа строку
    try:
        query = input('Enter query: ').lower()
        amount = int(input('Enter desired amount: '))

        start = time()
        downloader_videos(query, amount)
    # при ошибке выходим из программы
    except Exception as error:
        print('Wrong parameters have been entered!')
        print(f'Ha-ha-ha, you got the error: {error}')

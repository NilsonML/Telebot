from bs4 import BeautifulSoup
from time import sleep
from app.database.recept_table import async_session
from app.database import requests_for_parser as rqp

import pandas as pd
import requests
import asyncio

async def main():
    
    data = []
    need_categories = {'Завтраки':'zavtraki',
                'Основные блюда':'osnovnye-blyuda',
                'Бульоны':'bulony',
                'Супы':'supy',
                'Напитки':'napitki',
                'Салаты':'salaty'}

    def parse_recept_page(url_page):
        url = url_page
        nutrition_data = {}
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # print(url)
        nutritions = soup.select_one('span[itemprop="nutrition"]').find_all('span', itemprop=True)
        
        for span in nutritions:
            itemprop = span.get('itemprop')
            value = span.get_text(strip=True)
            nutrition_data[itemprop] = value        
        
        return [
            nutrition_data.get('calories'),
            nutrition_data.get('proteinContent'),
            nutrition_data.get('fatContent'),
            nutrition_data.get('carbohydrateContent')
        ]

    quantity_of_page = int(input("Введите количество страниц: "))

    main_url = "https://eda.ru/"
    response = requests.get(main_url)
    sleep(2)
    soup = BeautifulSoup(response.text, 'html.parser')
    elements = soup.find('div', class_="css-18mh8uc").find_all('span', class_="css-y44g8l")
        
    async with async_session() as session:
        for element in elements:
            name = element.contents[0]
            if name in need_categories:
                name_category = need_categories.get(name)
                cat_id = rqp.getter_create_category(name_category,session)
                url = main_url+'recepty/'+name_category
            else:
                continue
            for page in range(1,quantity_of_page+1):
                
                url_num_page = f"{url}?page={page}"
                response = requests.get(url_num_page)  # было requests.get(url): всегда грузилась 1-я страница
                sleep(2)
                soup = BeautifulSoup(response.text, 'html.parser')
                recipes = soup.find_all('div', class_="css-m0u77r")
                
                for rec in recipes:
                    name = rec.find('span',class_="css-1bs2jj2").text
                    portions = rec.find('span', class_="css-tqfyce").text
                    time = rec.find('span', class_="css-14gsni6").text
                    url_page = "https://eda.ru"+rec.find('a', class_="css-18hxz5k").get('href')
                    cpfc = parse_recept_page(url_page)
                    data.append([name, portions, time, *cpfc])

# header = ['name', 'portions', 'time', 'calories', 'protein', 'fats', 'carbohydrate']

# df = pd.DataFrame(data, columns=header)
# df.to_csv(r'C:\Users\user\Desktop\parser\eda_data.csv', sep=';', encoding='UTF-8-sig')

if __name__ == '__main__':
    asyncio.run(main())

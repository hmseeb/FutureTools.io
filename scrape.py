import asyncio
from selectolax.parser import HTMLParser
import time
import aiohttp
import sqlite3

baseurl = 'https://www.futuretools.io'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,',
}

conn = sqlite3.connect('futuretools.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS futuretools(title TEXT, description TEXT, category TEXT, featured_image TEXT, link TEXT, pricing_model TEXT)''')


async def homepage():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.jetboost.io/search?boosterId=cledf8e5d71pw0634gaia6sc4&q', headers=headers) as response:
            data = await response.json()
            urls = [
                f'https://www.futuretools.io/tools/{url}' for url in data.keys()]
    return urls


semaphore = asyncio.Semaphore(50)


async def main(urls):
    async with semaphore:
        connector = aiohttp.TCPConnector(limit=50)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for url in urls:
                task = asyncio.ensure_future(fetch(session, url))
                tasks.append(task)
                semaphore.release()
            await asyncio.gather(*tasks)


async def fetch(session, url):
    async with session.get(url, headers=headers) as response:
        await scrape(await response.text(), response.url)


async def scrape(response, url):

    parser = HTMLParser(response)

    try:
        title = parser.css_first('h1.heading-3').text()
        description = parser.css_first('div.rich-text-block').text()
        category = parser.css_first('div.text-block-18').text()
        image = parser.css_first('img.image-3').attributes['src']
        link = parser.css_first('a.link-block-2').attributes['href']
        model = parser.css_first('div.text-block-2').text()

        cursor.execute('''INSERT INTO futuretools VALUES (?,?,?,?,?,?)''',
                       (title, description, category, image, link, model))
        conn.commit()
    except Exception as e:
        print(f'Error: {e} \nURL: {url}')


if __name__ == '__main__':
    print('Started scraper..')
    start_time = time.time()
    urls = asyncio.run(homepage())
    asyncio.run(main(urls))
    print(f'Elapsed time: {int(time.time() - start_time)} seconds')

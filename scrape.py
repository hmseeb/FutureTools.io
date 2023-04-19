import asyncio
from pyppeteer import launch
from selectolax.parser import HTMLParser
import time
import aiohttp
import sqlite3

baseurl = 'https://www.futuretools.io'

conn = sqlite3.connect('tools.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS tools(title TEXT, description TEXT, category TEXT, featured_image TEXT, link TEXT, pricing_model TEXT)''')


async def homepage():

    scraper = await launch()
    page = await scraper.newPage()
    await page.goto(baseurl)

    SCROLL_PAUSE_TIME = 0.5

    last_height = await page.evaluate('document.body.scrollHeight')

    while True:
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight);')
        await asyncio.sleep(SCROLL_PAUSE_TIME)
        new_height = await page.evaluate('document.body.scrollHeight')
        if new_height == last_height:
            break
        last_height = new_height
    # Get the page content and parse it

    content = await page.content()
    parser = HTMLParser(content)
    urls = []
    for c in parser.css('div.tool-item-text-link-block---new'):
        urls.append(baseurl + c.css('a')[0].attributes['href'])
    await scraper.close()
    return urls


async def main(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            task = asyncio.ensure_future(fetch(session, url))
            tasks.append(task)
        await asyncio.gather(*tasks)


async def fetch(session, url):
    async with session.get(url) as response:
        await scrape(await response.text())


async def scrape(response):

    parser = HTMLParser(response)

    try:
        title = parser.css_first('h1.heading-3').text()
        description = parser.css_first('div.rich-text-block').text()
        category = parser.css_first('div.text-block-18').text()
        featured_image = parser.css_first('img.image-3').attributes['src']
        link = parser.css_first('a.link-block-2').attributes['href']
        pricing_model = parser.css_first('div.text-block-2').text()

        cursor.execute('''INSERT INTO tools VALUES (?,?,?,?,?,?)''',
                       (title, description, category, featured_image, link, pricing_model))
        conn.commit()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    print('Started scraper..')
    start_time = time.time()
    urls = asyncio.run(homepage())
    asyncio.run(main(urls))
    print(f'Elapsed time: {int(time.time() - start_time)} seconds')

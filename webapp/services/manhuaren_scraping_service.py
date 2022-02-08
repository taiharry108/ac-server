import string
import dataclasses
from logging import getLogger
from pathlib import Path
import re
from typing import List
from webapp.models.chapter import Chapter

from webapp.models.manga import Manga
from webapp.models.manga_index_type_enum import MangaIndexTypeEnum

from webapp.models.manga_site import MangaSite

from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService
from webapp.services.utils import convert_url

logger = getLogger(__name__)


digs = string.digits + string.ascii_letters


def int2base(x, base):
    if x < 0:
        sign = -1
    elif x == 0:
        return digs[0]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(digs[int(x % base)])
        x = int(x / base)

    if sign < 0:
        digits.append('-')

    digits.reverse()

    return ''.join(digits)


def decode(p, a: int, c: int, k, d):
    def e(c: int) -> str:
        first = "" if c < a else e(int(c/a))
        c = c % a
        if c > 35:
            second = chr(c + 29)
        else:
            second = int2base(c, 36)
        return first + second
    while c != 0:
        c -= 1
        d[e(c)] = k[c] if k[c] != "" else e(c)
    k = [lambda x: d[x]]
    def e2(): return '\\w+'
    c = 1
    while c != 0:
        c -= 1
        p = re.sub(f'\\b{e2()}\\b', lambda x: k[c](x.group()), p)
    return p


@dataclasses.dataclass
class ManhuarenScrapingService(AbstractMangaSiteScrapingService):
    site: MangaSite = MangaSite(
        id=0, name="manhuaren", url="https://www.manhuaren.com/")

    async def search_manga(self, keyword: str) -> List[Manga]:
        """Search manga with keyword, return a list of manga"""
        def handle_div(div) -> Manga:
            name = div.find('p', class_='book-list-info-title').text
            url = div.find('a').get('href')
            url = convert_url(url, self.url)

            return Manga(name=name, url=url)

        search_url = f'{self.site.url}search?title={keyword}&language=1'
        soup = await self.download_service.get_soup(search_url)
        result = [handle_div(d) for d in soup.find('ul', class_='book-list').find_all(
            'div', class_='book-list-info')]
        return result

    @property
    def url(self):
        return self.site.url

    def get_meta_data(self, soup):
        div = soup.find(
            'div', {'id': 'tempc'}).find('div', class_='detail-list-title')
        last_update = div.find(
            'span', class_='detail-list-title-3').text.strip()
        finished = div.find('span', class_='detail-list-title-1').text == '已完结'
        thum_img = soup.find('img', class_='detail-main-bg').get('src')

        convert_url(thum_img, self.url)

        return {'last_update': last_update, 'finished': finished, 'thum_img': thum_img}

    async def get_index_page(self, manga: Manga) -> Manga:
        """Get index page of manga, return a manga with chapters"""
        def get_type(idx_type):
            if idx_type == '连载':
                type_ = MangaIndexTypeEnum.CHAPTER
            elif idx_type == '单行本':
                type_ = MangaIndexTypeEnum.VOLUME
            else:
                type_ = MangaIndexTypeEnum.MISC
            return type_

        soup = await self.download_service.get_soup(manga.url)

        div = soup.find('div', class_='detail-selector')

        id_dict = {}

        for a in div.find_all('a', 'detail-selector-item'):
            onclick = a.get('onclick')
            if 'titleSelect' in onclick:
                id_dict[a.text] = onclick.split("'")[3]
        for idx_type, id_v in id_dict.items():
            ul = soup.find('ul', {'id': id_v})
            m_type = get_type(idx_type)
            for a in reversed(ul.find_all('a')):
                url = a.get('href')
                url = convert_url(url, self.url)
                title = a.text
                manga.add_chapter(m_type=m_type, title=title, page_url=url)

        meta_dict = self.get_meta_data(soup)
        thum_img_path = await self.download_service.download_img(meta_dict['thum_img'], download_path=Path("thum_img"), filename=self.create_img_name(manga))
        meta_dict['thum_img'] = thum_img_path['pic_path']

        manga.set_meta_data(meta_dict)
        manga.retreived_idx_page()
        return manga

    async def get_page_urls(self, chapter: Chapter) -> List[str]:
        """Get all the urls of a chaper, return a list of strings"""
        soup = await self.download_service.get_soup(chapter.page_url)

        match = None
        for script in soup.find_all('script'):
            if len(script.contents) == 0:
                continue
            if script.contents[0].startswith('eval'):
                match = re.search('return p;}(.*\))\)', script.contents[0])
                break
        if match:
            tuple_str = match.group(1)
            p, a, c, k, e, d = eval(tuple_str)
            p = decode(p, a, c, k, d)

            match2 = re.search(r'var newImgs=(.*);', p)
            if match2:
                pages = eval(match2.group(1))
                return pages
        return []    
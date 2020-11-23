import requests
from bs4 import BeautifulSoup
import re

from Classes.Utils import Utils


class Barnehager:

    def __init__(self, link):
        self.page = requests.get(link)
        self.soup = BeautifulSoup(self.page.content, 'html.parser')
        self.bydeler = re.findall('<h2>(.+?)</h2>', str(self.soup))
        self.tables = self.soup.find_all('table')
        self.data = Utils.create_full_df(self)  # .set_index(df.groupby(level=0).cumcount(), append=True)
        self.dataframe = self.data[0]
        self.foreldreundersokelse = self.data[1]


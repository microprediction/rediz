from bs4 import BeautifulSoup
import re
import json
import logging
import requests

# Forked from https://github.com/BlankerL/DXY-COVID-19-Crawler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
}

country_type = {
    1: '中国'
}

uri = '**Confidential**'


def apply():
    f = Fetcher()
    stuff = f.get()
    return stuff

FIELDS = ('currentConfirmedCount', 'confirmedCount', 'suspectedCount', 'curedCount', 'deadCount')

class Fetcher:

    def get(self):
        r = requests.get(url='https://3g.dxy.cn/newh5/view/pneumonia')
        soup = BeautifulSoup(r.content, 'lxml')
        overall_information = re.search(r'\{("id".*?)\]\}',
                                        str(soup.find('script', attrs={'id': 'getStatisticsService'})))
        province_information = re.search(r'\[(.*?)\]',
                                         str(soup.find('script', attrs={'id': 'getListByCountryTypeService1'})))
        area_information = re.search(r'\[(.*)\]', str(soup.find('script', attrs={'id': 'getAreaStat'})))

        parsed = dict()
        parsed['overall']= self.overall_parser(overall_information=overall_information)
        if True:
            parsed['provincial'] = self.province_parser(province_information=province_information)
        return parsed

    def overall_parser(self, overall_information):
        overall_information = json.loads(overall_information.group(0))
        overall_information.pop('id')
        overall_information.pop('createTime')
        overall_information.pop('modifyTime')
        overall_information.pop('imgUrl')
        overall_information.pop('deleted')
        overall_information['countRemark'] = overall_information['countRemark'].replace(' 疑似', '，疑似').replace(' 治愈',
                                                                                                              '，治愈').replace(
            ' 死亡', '，死亡').replace(' ', '')
        overall_information = dict( [ (f, overall_information[f]) for f in FIELDS ] )
        return overall_information

    def province_parser(self, province_information):
        provinces = json.loads(province_information.group(0))
        provinces_data = dict( [ (f,list()) for f in FIELDS ] )
        provinces_data.update( {"names":list()})
        for province_no, province in enumerate(provinces):
            province.pop('id')
            province.pop('tags')
            province.pop('sort')
            province['comment'] = province['comment'].replace(' ', '')
            province['country'] = country_type.get(province['countryType'])
            for f in FIELDS:
                provinces_data[f].append(province[f])
            provinces_data["names"].append( province["provinceName"] )
        return provinces_data



if __name__ == '__main__':
    data = apply()

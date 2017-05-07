import pymongo
import requests
import re
import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver


class MoocLink(object):
    def __init__(self, name):
        client = pymongo.MongoClient('localhost')
        db = client['MOOC']
        self.coll = db[name]
        self.name = name

    def searchMooc(self):
        """
        使用selenium可以不需要登录就能获得课程的地址，但不能获得每一节可的详细信息
        """
        driver = webdriver.PhantomJS()
        name = str(self.name.encode('utf-8')).replace(r'\x', '%').replace('b', '', 1).replace('\'', '').split('%', 1)
        lession = name[0] + '%' + name[1].upper()
        url = 'http://www.icourse163.org/search.htm?search={0}#/'.format(lession)
        driver.get(url)
        time.sleep(1)
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        toal = soup.findAll('div', {'class': 'u-clist f-bg f-cb f-pr j-href ga-click'})
        print('看看你要的是哪门课')
        print('看中哪门请把它copy到接下来的提示中,回车就OK了。。。')

        for t in toal:
            href = t['data-href'].replace('course', 'learn')
            le_na = t.get_text()
            print(f'网页：{href}  -----课程：{le_na}')

    def getMocTermDto(self):
        if not self.coll.find_one({'_id': self.name}):
            self.searchMooc()
            whichname = input('好了输入你要的网页链接：')
            header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/538.1 (KHTML, like Gecko) '
                                    'PhantomJS/2.1.1 Safari/538.1'}
            url = 'http://www.icourse163.org' + whichname
            res = requests.get(url, headers=header)
            res.encoding = 'utf-8'
            html = res.text
            self.coll.update({'_id': self.name}, dict(_id=self.name, html=html), True)
        else:
            html = self.coll.find_one({'_id': self.name})['html']
        pattern = r'window.termDto = {\s.*'
        id = re.search(r'\d+', re.search(pattern, html).group(0))
        return id.group(0)

    def getParam(self):
        param = []
        #  httpsession没能找到是从哪里给出的
        httpsession = ['528e85ac4d9d4eb8952725c0728b9dd6', '1c5f77d1b77b40feace514a4ec220ce6',
                       'e1392fd7f8eb43198c77ee465e758ff8']
        c0 = self.getMocTermDto()
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:49.0) Gecko/20100101 Firefox/49.0'}
        url = "http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLastLearnedMocTermDto.dwr"
        data = {'callCount': '1',
                'scriptSessionId': '${scriptSessionId}190',
                'httpSessionId': random.choice(httpsession),
                'c0-scriptName': 'CourseBean',
                'c0-methodName': 'getMocTermDto',
                'c0-id': '0',
                'c0-param0': 'number:' + str(c0),
                'c0-param1': 'number:0',
                'c0-param2': 'boolean:true',
                'batchId': str(time.time())[:13].replace('.', '')
        }
        res = requests.post(url, headers=header, data=data)
        res.encoding = 'utf-8'
        html = res.text
        pattern = r'contentId=\d+.*?id=\d+'
        contentId = re.findall(pattern, html)
        for i in contentId:
            try:
                c0param0 = re.search(r'\d+', i).group(0)
                c0param3 = re.search(r'\d+', re.search(r'id=\d+', i).group(0)).group(0)
                param.append((c0param0, c0param3))
            except:
                pass
        return param

    def getFlv(self):
        _id = 0
        c0param = self.getParam()
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'}
        url = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr'
        for c0, c3 in c0param:

            time.sleep(0.5)
            data = {
                'callCount': '1',
                'scriptSessionId': '${scriptSessionId}190',
                'httpSessionId': 'ade9cdfb6728417b950752011d5fb068',
                'c0-scriptName': 'CourseBean',
                'c0-methodName': 'getLessonUnitLearnVo',
                'c0-id': '0',
                'c0-param0': 'number:' + str(c0),
                'c0-param1': 'number:1',
                'c0-param2': 'number:0',
                'c0-param3': 'number:' + str(c3),
                'batchId': str(time.time())[:13].replace('.', '')
            }

            res = requests.post(url=url, headers=header, data=data)
            html = res.text
            pattern = r'http.*?"'
            try:
                videos = ['超清flv', '高清flv', '标清flv', '超清mp4', '高清mp4', '标清mp4']
                linkfm = re.findall(pattern, html)
                hfm = []
                for fm in zip(videos, linkfm[:6]):
                    hfm.append(fm)
                hfmd = dict(hfm)
                ni = dict(name=self.name)
                ni.update(hfmd)
                if ni[videos[0]]:
                    _id += 1
                    ni.update(dict(_id=_id))
                    self.coll.insert_one(ni)
                else:
                    pass
            except Exception as e:
                print(e)
        print('好了数据都有了等着下就是了。。。')

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

    def _pymongodb(self, datas):
        client = pymongo.MongoClient('localhost')
        db = client['MOOC']
        coll = db[self.name]
        coll.insert_one(datas)
        client.close()

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
            print("正在查找课件。。。"
                  "大概需要等。。。"
                  "我也不知道。。。")
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
        detail = []

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
        until_name = []

        pattern0 = r'homeworks'
        pattern1 = r'chapterId.*?units'
        pattern2 = r'contentId=\d+.*name=.*?;'
        pattern3 = r'name=".*?;'
        sp_text = re.split(pattern0, html)
        for sp in sp_text[1:]:
            untis = re.findall(pattern1, sp)
            week_name = bytes(ord(i) for i in re.search(pattern3, sp).group(0)[6:-1].replace('"', '')).decode(
                'unicode_escape')
            for u in untis:
                u_name = bytes(ord(i) for i in re.search(pattern3, u).group(0)[6:-2].replace(r'\\', '\\')).decode(
                    'unicode_escape')
                until_name.append(u_name)
            unti = re.split(pattern1, sp)[1:]
            for iu in range(len(unti)):
                cont = re.findall(pattern2, unti[iu])
                for i in cont:
                    param = []
                    c0param0 = re.search(r'\d+', i).group(0)
                    c0param1 = re.search(r'\d+', re.search(r'contentType=\d+', i).group(0)).group(0)
                    c0param3 = re.search(r'\d+', re.search(r'id=\d+', i).group(0)).group(0)
                    name = bytes(
                        ord(i) for i in re.search(r'name=".*?;', i).group(0)[6:-2].replace(r'\\', '\\')).decode(
                        'unicode_escape')
                    param.append((week_name, until_name[iu], name, c0param0, c0param1, c0param3))
                    detail.append(param)
        return detail

    def getFlv(self):
        """c1 = [1, 3, 4]
              1----Video
              3----pdf
              4----text"""
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'}
        url = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr'
        c0param = self.getParam()
        for param in c0param:
            for week_name, until_name, course_name, c0, c1, c3 in param:
                names = [week_name, until_name, course_name]
                time.sleep(0.2)
                data = {
                    'callCount': '1',
                    'scriptSessionId': '${scriptSessionId}190',
                    'httpSessionId': 'ade9cdfb6728417b950752011d5fb068',
                    'c0-scriptName': 'CourseBean',
                    'c0-methodName': 'getLessonUnitLearnVo',
                    'c0-id': '0',
                    'c0-param0': 'number:' + str(c0),
                    'c0-param1': 'number:' + str(c1),
                    'c0-param2': 'number:0',
                    'c0-param3': 'number:' + str(c3),
                    'batchId': str(time.time())[:13].replace('.', '')
                }

                res = requests.post(url=url, headers=header, data=data)
                content = res.text
                if str(c1) == str(1):
                    patV = r'http.*?"'
                    try:
                        Video_re = re.findall(patV, content)
                        self._getVideo(Video_re, names)
                    except:
                        continue
                elif str(c1) == str(3):
                    patP = r'textOrigUrl:"http.*?"'
                    try:
                        PDF_re = re.search(patP, content).group(0)
                        self._getPdf(PDF_re[13:], names)
                    except:
                        continue
                elif str(c1) == str(4):
                    patT = r'htmlContent:"<p>.*?(</p>)'
                    try:
                        TEXT_re = re.search(patT, content).group(0)
                        self._getText(TEXT_re[13:-1], names)
                    except:
                        continue
                else:
                    pass

    def _getVideo(self, content, nd):
        names = dict(week_name=nd[0], until_name=nd[1], course_name=nd[2])
        videos = ['超清flv', '高清flv', '标清flv', '超清mp4', '高清mp4', '标清mp4']
        linkfm = content
        hfm = []
        for fm in zip(videos, linkfm[:6]):
            hfm.append(fm)
        hfmd = dict(hfm)
        ni = dict(name=self.name)
        ni.update(hfmd)
        if ni[videos[0]]:
            ni.update(names)
            self._pymongodb(ni)

    def _getPdf(self, content, nd):

        data = dict(week_name=nd[0], until_name=nd[1], course_name=nd[2], name='pdf', pdf=content)
        self._pymongodb(data)

    def _getText(self, content, nd):
        soup = BeautifulSoup(content, 'lxml')
        text = soup.find('p').get_text()
        data = dict(week_name=nd[0], until_name=nd[1], course_name=nd[2], name='text', text=text)
        self._pymongodb(data)

if __name__ == '__main__':
    mooclink = MoocLink('Python机器学习应用')
    mooclink.getFlv()

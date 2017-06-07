# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from selenium import webdriver
from mongosave import Mongo
import random
import requests
import time
import re



class study163(object):
    def __init__(self, name):
        self.mongo = Mongo()
        self.name = name
        httpSessionId = ['59d5a8605b9f4472aac02d78cb3aaad0',
                         'b66db18f5af6438fbb242729c4d3f2a2',
                         'f8bb614167ed45779b7a05b5def8e55d']
        self.sessionId = random.choice(httpSessionId)

    def getCouseId(self):
        course_id = []
        course_name = []
        search = self.name
        print("正在检索...")
        name = str(search.encode('utf-8')).replace(r'\x', '%').replace('b', '', 1).replace('\'', '').split('%', 1)
        lession = name[0] + '%' + name[1].upper()
        url = 'http://study.163.com/courses-search?keyword={0}'
        driver = webdriver.PhantomJS()
        driver.get(url.format(lession))
        time.sleep(1)
        html = driver.page_source
        pattern = r'j-href.*//study.163.com/course/introduction/\d+.htm'
        page = re.findall(pattern, html)
        for i in page:
            p0 = r'/\d+'
            courseId = re.search(p0, i).group(0).replace('/', '')
            course_id.append(courseId)
        pa = r'<h3 class="">.*?</h3>'
        h3 = re.findall(pa, html)
        for h in h3:
            p1 = r'>.*<'
            name = re.search(p1, h).group(0).replace('>', '').replace('<', '')
            course_name.append(name)
        course_dict = dict([d for d in zip(course_name, course_id)])
        dicts = dict()
        if search in course_dict:
            dicts[str(search)] = course_dict[search]
            print(dicts)
            print('已经找到这门课了。')
            return dicts
        else:
            for k in course_dict:
                print(k)
            s = input('输入你要下载的课程(请记住，以防出现错误时，再次下载使用)：')
            if s in course_dict:
                dicts[str(s)] = course_dict[s]
                return dicts
            else:
                print('没有这么课，你再仔细看下。')

    def getPlanCourseDetail(self):
        course = self.getCouseId()
        for i in course:
            course_name = i
            courseId = course[i]
        data = {'callCount': '1',
                'scriptSessionId': '${scriptSessionId}190',
                'httpSessionId': str(self.sessionId),
                'c0-scriptName': 'PlanNewBean',
                'c0-methodName': 'getPlanCourseDetail',
                'c0-id': '0',
                'c0-param0': 'string:' + str(courseId),
                'c0-param1': 'number:0',
                'c0-param2': 'null:null',
                'batchId': str(time.time())[:13].replace('.', '')
                }
        header = {'Cache-Control': 'max-age=0',
                  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
                  'Content-Type': 'text/javascript',
                  'Referer': 'http://study.163.com/course/introduction.htm?courseId=' + str(courseId)
                  }
        url = "http://study.163.com/dwr/call/plaincall/PlanNewBean.getPlanCourseDetail.dwr?{0}"
        res = requests.post(url.format(str(time.time())[:13].replace('.', '')), headers=header, data=data)
        pattern0 = r'audioTime.*?wapUrl'
        pattern1 = r'id=\d+'
        pattern2 = r'lessonName=".*?;'
        audiotime = re.findall(pattern0, res.text)
        details = dict()
        for i in audiotime:
            id = re.search(pattern1, i).group(0)[3:]
            b = re.search(pattern2, i).group(0)[12:-2]
            lession_name = bytes(ord(i) for i in b).decode('unicode_escape')
            details[id] = lession_name
            print('找到' + course_name + '内容：' + lession_name)
        return [details, courseId, course_name]

    def getVideoInfo(self):
        url = "http://study.163.com/dwr/call/plaincall/LessonLearnBean.getVideoLearnInfo.dwr?{0}"
        detail, courseId, course_name = self.getPlanCourseDetail()
        for i in detail:
            data = {'callCount': '1',
                    'scriptSessionId': '${scriptSessionId}190',
                    'httpSessionId': str(self.sessionId),
                    'c0-scriptName': 'LessonLearnBean',
                    'c0-methodName': 'getVideoLearnInfo',
                    'c0-id': '0',
                    'c0-param0': 'string:' + str(i),
                    'c0-param1': 'string:' + str(courseId),
                    'batchId': str(time.time())[:13].replace('.', '')
                    }
            header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
                      'Content-Type': 'text/javascript'}
            res = requests.post(url.format(str(time.time())[:13].replace('.', '')), headers=header, data=data)
            patV = r'http.*?"'
            videos = ['超清flv', '高清flv', '标清flv', '超清mp4', '高清mp4', '标清mp4']
            try:
                Video_re = re.findall(patV, res.text)
                hfm = []
                for fm in zip(videos, Video_re):
                    hfm.append(fm)
                hfm.append(('course_name', detail[i]))
                hfm.append(('name', course_name))
                v_data = dict(hfm)
                self.mongo.save(v_data)
                print(v_data)
            except:
                continue



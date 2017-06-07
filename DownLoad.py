#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
'''
Required
- requests, mongodb
Info
- author : "starryj"
- date   : "2017.5.8"
'''

import requests
import pymongo
import os
from contextlib import closing
from mooc import MoocLink
from study163 import study163
from progressbar import ProgressBar
from multiprocessing import Pool


class MoocDown(object):
    def __init__(self):
        self.client = pymongo.MongoClient('localhost')
        self.db_mooc = self.client['MOOC']
        self.db_study = self.client['study163']

    @staticmethod
    def videoDown(class_name, video_href, video_type, td, detail_name):
        path = os.path.join('D:\DATAS\MOOC Videos\\', class_name)
        if not os.path.exists(path):
            os.mkdir(path)
        if td == '0':
            cl = 'MOOC'
            week_name, until_name, course_name = detail_name
            path0 = os.path.join(path, week_name)
            if not os.path.exists(path0):
                os.mkdir(path0)
            path1 = os.path.join(path0, until_name)
            if not os.path.exists(path1):
                os.mkdir(path1)
            video_path = os.path.join(path1, course_name + '.' + video_type)
        else:
            cl = 'study163'
            course_name = detail_name
            video_path = os.path.join(path, str(course_name) + '.' + video_type)
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'}
        try:
            with closing(requests.get(url=video_href, headers=header, stream=True)) as response:
                count_size = int(response.headers['Content-Length'])
                chunk_size = 1024*4
                p = ProgressBar(total=count_size, name=course_name)
                for i in response.iter_content(chunk_size):
                    with open(video_path, 'ab') as f:
                        f.write(i)
                    p.log(len(i))
            client = pymongo.MongoClient('localhost')
            db = client[cl]
            db[class_name].remove({'course_name': course_name})
            client.close()
        except Exception as E:
            print(E)

    def mooc(self, video='超清flv'):
        video_href = []
        pdf_href = []
        v_name = []
        p_name = []
        class_name = input("输入你正在找的课程(Mooc)：")

        coll = self.db_mooc[class_name]
        V_links = coll.find({'name': class_name})
        P_links = coll.find({'name': 'pdf'})
        T_texts = coll.find({'name': 'text'})
        if str(V_links.count()) == '0' and str(P_links.count()) == '0' and str(T_texts.count()) == '0':
            ml = MoocLink(class_name)
            ml.getFlv()
            coll = self.db_mooc[class_name]
            V_links = coll.find({'name': class_name})
            P_links = coll.find({'name': 'pdf'})
            T_texts = coll.find({'name': 'text'})
        vt = video[2:]
        for v in V_links:
            video_href.append(v[video])
            v_name.append((v['week_name'], v['until_name'], v['course_name']))
        for p in P_links:
            pdf_href.append(p['pdf'])
            p_name.append((p['week_name'], p['until_name'], p['course_name']))
        path1 = os.path.join('D:\DATAS\MOOC Videos\\', class_name)
        if not os.path.exists(path1):
            os.mkdir(path1)
        print('正在下载富文本文件')
        for t in T_texts:
            print(t)
            path0 = os.path.join(path1, t['week_name'])
            if not os.path.exists(path0):
                os.mkdir(path0)
            path1 = os.path.join(path0, t['until_name'])
            if not os.path.exists(path1):
                os.mkdir(path1)
            t_path = os.path.join(path1, t['course_name'] + '.py')
            with open(t_path, 'w', encoding='utf-8') as f:
                f.write(t['text'].replace(r'\n', '\n'))
                print('成功下载富文本文件----' + str(t['course_name']))
        self.client.close()
        pool1 = Pool(4)
        try:
            print('正在下载视频课件')
            for h in range(len(video_href)):
                pool1.apply_async(func=self.videoDown, args=(class_name, video_href[h], vt, '0', v_name[h]))
            pool1.close()
            pool1.join()
        except Exception as e:
            print(e)
        pool2 = Pool(4)
        try:
            print('正在下载pdf课件')
            for p in range(len(pdf_href)):
                pool2.apply_async(func=self.videoDown, args=(class_name, pdf_href[p], 'pdf', '0', p_name[p]))
            pool2.close()
            pool2.join()
        except Exception as e:
            print(e)

    def study(self, video='超清flv'):
        href = []
        course_name = []
        class_name = input("输入你正在找的课程(study163)：")
        coll = self.db_study[class_name]
        links = coll.find({})
        self.client.close()
        vt = video[2:]
        path1 = os.path.join('D:\DATAS\MOOC Videos\\', class_name)
        if not os.path.exists(path1):
            os.mkdir(path1)
        if str(links.count()) == '0':
            study = study163(name=class_name)
            study.getVideoInfo()
            coll = self.db_study[class_name]
            links = coll.find({})
            self.client.close()
        for link in links:
            href.append(link[video])
            course_name.append(link['course_name'])
        pool = Pool(4)
        try:
            print('正在下载视频课件')
            for h in range(len(href)):
                pool.apply_async(func=self.videoDown, args=(class_name, href[h], vt, '1', course_name[h]))
            pool.close()
            pool.join()
        except Exception as e:
            print(e)

    def download(self, where):
        """0 表示使用Mooc
           1 表示使用Study163
           others is None"""
        if str(where) == '0':
            self.mooc()
        elif str(where) == '1':
            self.study()
        else:
            print('ERROR')

if __name__ == '__main__':
    mooc = MoocDown()
    mooc.download(where=0)

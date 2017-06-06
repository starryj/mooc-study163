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


class CourseDown(object):
    def __init__(self):
        self.client = pymongo.MongoClient('localhost')
        self.db_mooc = self.client['MOOC']
        self.db_study = self.client['study163']

    @staticmethod
    def videoDown(video_name, video_href, video_id, video_type, td):
        path1 = os.path.join('D:\DATAS\MOOC Videos\\', video_name)
        if not os.path.exists(path1):
            os.mkdir(path1)
        if td == '0':
            cl = 'MOOC'
            path = os.path.join(path1, video_name + str(video_id) + '.' + video_type)
        else:
            cl = 'study163'
            path = os.path.join(path1, str(video_id) + '.' + video_type)
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'}
        if os.path.exists(path):
            os.remove(path)
        try:
            with closing(requests.get(url=video_href, headers=header, stream=True)) as response:
                count_size = int(response.headers['Content-Length'])
                chunk_size = 1024*4
                p = ProgressBar(total=count_size, name=video_name + str(video_id))
                for i in response.iter_content(chunk_size):
                    with open(path, 'ab') as f:
                        f.write(i)
                    p.log(len(i))
            client = pymongo.MongoClient('localhost')
            db = client[cl]
            db[video_name].remove({'_id': video_id})
            client.close()
        except Exception as E:
            print(E)

    def mooc(self, video='超清flv'):
        href = []
        ids = []
        p_href = []
        p_ids = []
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
        for link in V_links:
            href.append(link[video])
            ids.append(link['_id'])
        for P_link in P_links:
            p_href.append(P_link['pdf'])
            p_ids.append(P_link['_id'])
        path1 = os.path.join('D:\DATAS\MOOC Videos\\', class_name)
        if not os.path.exists(path1):
            os.mkdir(path1)
        print('正在下载富文本文件')
        for texts in T_texts:
            text_id = texts['_id']
            path = os.path.join(path1, class_name + str(text_id) + '.txt')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(texts['text'])
                print('成功下载富文本文件----' + str(text_id))
        self.client.close()
        pool1 = Pool(4)
        try:
            print('正在下载视频课件')
            for h in range(len(href)):
                pool1.apply_async(func=self.videoDown, args=(class_name, href[h], ids[h], vt, '0'))
            pool1.close()
            pool1.join()
        except Exception as e:
            print(e)
        pool2 = Pool(4)
        try:
            print('正在下载pdf课件')
            for p in range(len(p_href)):
                pool2.apply_async(func=self.videoDown, args=(class_name, p_href[p], p_ids[p], 'pdf', '0'))
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
            course_name.append(link['_id'])
        pool = Pool(4)
        try:
            print('正在下载视频课件')
            for h in range(len(href)):
                pool.apply_async(func=self.videoDown, args=(class_name, href[h], course_name[h], vt, '1'))
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
    mooc = CourseDown()
    mooc.download(where=0)

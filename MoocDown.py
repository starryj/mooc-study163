import requests
import pymongo
import os
from contextlib import closing
from mooclinks import MoocLink
from progressbar import ProgressBar
from multiprocessing import Pool


class MoocDown(object):
    def __init__(self):
        self.client = pymongo.MongoClient('localhost')
        self.db = self.client['MOOC']

    @staticmethod
    def videoDown(video_name, video_href, video_id, video_type):
        path1 = os.path.join('D:\DATAS\MOOC Videos\\', video_name)
        if not os.path.exists(path1):
            os.mkdir(path1)
        path = path1 + video_name + str(video_id) + '.' + video_type
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
            db = client['MOOC']
            db[video_name].remove({'link': video_href})
            client.close()
        except Exception as E:
            print(E)

    def Down(self):
        href = []
        ids = []
        class_name = input("输入你正在找的课程：")

        coll = self.db[class_name]
        links = coll.find({'name': class_name})
        if str(links.count()) == '0:
            ml = MoocLink(class_name)
            ml.getFlv()
            coll = self.db[class_name]
            links = coll.find({'name': class_name})
        videos = ['超清flv', '高清flv', '标清flv', '超清mp4', '高清mp4', '标清mp4']
        print('你想下载哪种格式的视频', videos)
        video = input('输入你要下载的格式（回车）：')

        vt = video[2:]
        for link in links:
            href.append(link[video])
            ids.append(link['_id'])
        self.client.close()
        pool = Pool(4)
        try:
            for h in range(len(href)):
                pool.apply_async(func=self.videoDown, args=(class_name, href[h], ids[h], vt))
            pool.close()
            pool.join()
        except Exception as e:
            print(e)


if __name__ == '__main__':
    mooc = MoocDown()
    mooc.Down()

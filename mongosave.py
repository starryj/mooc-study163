import pymongo


class Mongo(object):
    def __init__(self):
        pass

    def save(self, datas):
        name = datas['name']
        client = pymongo.MongoClient('localhost')
        db = client['study163']
        collection = db[name]
        collection.insert_one(datas)
        client.close()

    def find(self, eq):
        pass
if __name__ == '__main__':
    m = Mongo()
    m.save(dict(_id='PPT页面的黑色质感方块设计', name='name'))
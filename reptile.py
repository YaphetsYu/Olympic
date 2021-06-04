import requests
import time
import hashlib
import json
import unicodedata
import os
import random
import glob
import tqdm
from Knowledge import OlympicKnowledge

def write_data(data, data_path="text_train", label_path="label_train"):
    with open(data_path, "w") as f1, open(label_path, "w") as f2:
        for d, label in data:
            f1.write("{}\n".format(d))
            f2.write("{}\n".format(" ".join(label)))


class Database(object):

    def __init__(self):
        self.source = {
        "新闻": "9dba1061df9685558ab9030b817e77b9",
        "微博": "c1c1767f56d8d61c83684de45e6daa12",
        "twitter": "33062ffc6de6b58b6652e4c2e3f30ed2",
        "facebook": "cfe794e349db1356a045680e32c576c0",
        "APP": "81c5f8e1849938c3290173e0a479eb1c",
        "短视频": "40c19a0b482305ee5c9de9479c558559",
        "电子报纸": "6f8197a4b42d52d5c2bb913e327c31b1",
        "微信": "af0353de65c0d156bb317043666f25e3"}
        self.project = ["短道速滑","速度滑冰","花样滑冰","冰壶","冰球",
                        "自由式滑雪","冬季两项", "北欧两项", "无舵雪橇","有舵雪橇",
                        "钢架雪车", "俯式冰橇", "单板滑雪", "高山滑雪", "平昌冬奥会",
                        "越野滑雪", "跳台滑雪", "俯式冰橇"]
        # 北欧两项 (越野滑雪、跳台滑雪)
        # 钢架雪车 (俯式冰橇)
        self.knowledge = OlympicKnowledge()
        self.appKey = "hCzMvxeX"
        self.appSecret = "c33a929446fb2e299f99be0d922964a48fffeca9"
        self.url = "http://wenhai.wengegroup.com/wenhai-api/subscribe/getByGid"
        self.database = "./dataset"
        self.time_start = "2020-05-01 00:00:00"
        self.maxsize = 100000
        self.PostHeader = {}


    def CreateHeader(self):
        curtime = int(time.time() * 1000)
        self.PostHeader["appKey"] = self.appKey
        self.PostHeader["timeStamp"] = str(curtime)
        sign = self.appKey + str(curtime) + self.appSecret
        sign = hashlib.sha256(sign.encode("utf-8")).hexdigest()
        self.PostHeader["sign"] = sign
        return self.PostHeader

    def getPieceDataExample(self, tag, start_time=time.strftime("%Y-%m-%d 08:00:00", time.localtime()),
                        end_time=time.strftime("%Y-%m-%d 21:00:00", time.localtime()),
                     sort_way="asc", page_size=20, gid=0):
        """
        :param tag: source sub id, which data source to get
        :param start_time:The starting time of article publishing is the same day by default
        :param end_time:The end time of the article publishing, the default end time of the article publishing on the same day
        :param sort_way:sort order, asc default, desc opt.
        :param page_size:Number of items per page: 1-50, 20 by default
        :param gid:Cursor (primary key of data), used for page turning.
                   The first page can be set to 0, and the previous page is used for page turning
        :remark 1. Subscribe to sub_ID cannot be empty
                2. start_Time and end_Time, must be in the same month, the default day;
                   start time cannot be greater than end time;
                3. Press GID to turn pages and get data incrementally;
                4. By default, it is in GID ascending order;
        :return: response.
        """
        Data, self.PostHeader = dict(), self.CreateHeader()
        Data["sub_id"] = self.source[tag]
        Data["start_time"], Data["end_time"] = start_time, end_time
        Data["sort_way"], Data["page_size"], Data["gid"] = sort_way, page_size, gid
        response = requests.post(url=self.url, headers=self.PostHeader, data=json.dumps(Data))
        # print(response.content.decode("utf8"))
        content = json.loads(response.content.decode("utf-8"))
        if "data" in content:
            gids = [article["gid"] for article in content["data"]["articles"]]
            for article in content["data"]["articles"]:
                article["content"] = unicodedata.normalize('NFKC', article["content"])
            max_gid = max([g["gid"] for g in content["data"]["articles"]])

        return gids, max_gid
    

    def getDataframe(self, y, t, tag):
        Data = None
        if y > 0 and t <= 5:
            Data = {"sub_id": self.source[tag],
                    "start_time": "202{}-{}-01 00:00:00".format(str(y), "0" + str(t) if t < 10 else str(t)),
                    "end_time": "202{}-{}-30 21:00:00".format(str(y), "0" + str(t) if t < 10 else str(t)),
                    "page_size": 50, "gid": 0}
        elif y == 0 and t >= 5:
            Data = {"sub_id": self.source[tag],
                    "start_time": "202{}-{}-01 00:00:00".format(str(y), "0" + str(t) if t < 10 else str(t)),
                    "end_time": "202{}-{}-30 21:00:00".format(str(y), "0" + str(t) if t < 10 else str(t)),
                    "page_size": 50, "gid": 0}
        elif y > 0 and t == 6:
            Data = {"sub_id": self.source[tag],
                    "start_time": "202{}-{}-01 00:00:00".format(str(y), "0" + str(t) if t < 10 else str(t)),
                    "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "page_size": 50, "gid": 0}
        return Data

    def getOlympicData(self, tag):
        self.PostHeader = self.CreateHeader()
        print("source: {}".format(tag))
        if not os.path.exists(os.path.join(self.database, tag)):
            os.makedirs(os.path.join(self.database, tag))
        root = os.path.join(self.database, tag)

        for y in range(0, 2):
            for t in range(1, 13):
                Data = self.getDataframe(y, t, tag)
                if Data is None: continue
                rt = os.path.join(root, "{}_{}".format(Data["start_time"], Data["end_time"]))
                if not os.path.exists(rt):
                    with open(rt, "w+") as f:
                        cnt = 0
                        # 09-01 -> 09-30 01-01 -> 01-30
                        while cnt <= self.maxsize:
                            r = requests.post(url=self.url, headers=self.PostHeader, data=json.dumps(Data))
                            content = json.loads(r.content.decode("utf-8"))
                            if content and "data" in content.keys() and len(content["data"]["articles"]) != 0:
                                for i, article in enumerate(content["data"]["articles"]):
                                    if article["category"] == "体育":
                                        f.write(json.dumps(article) + "\n")
                                        cnt += 1
                                Data["gid"] = content["data"]["articles"][-1]["gid"]
                                # gc = [g for g in content["data"]["articles"] if g["category"] == "体育"]
                                # if gc: print(random.choice(gc))
                                print(cnt)
                            else:
                                print(content)
                                break
                else:
                    print("{} exist.".format(rt))


    def filterData(self, tag):
        root = os.path.join(self.database, tag)
        with open(os.path.join(root, "new_tags_data"), "w") as f2:
            for file in glob.glob(root + "/202*"):
                with open(file, "r") as f1:
                    for line in tqdm.tqdm(f1):
                        d = json.loads(line.strip())
                        d["tags"] = self.knowledge.create_tages(d["content"])
                        # if d["tags"]:
                        f2.write("{}\n".format(json.dumps(d)))


    def getOlympicTag(self, tag):
        root = os.path.join(self.database, tag)
        Tag, cnt, count, coverage,length_tag = {}, 0, 0, {}, 0
        with open(os.path.join(root, "new_tags_data"), "r") as f:
            for line in f:
                d = json.loads(line.strip())
                if "tags" in d and d["tags"]:
                    for t in d["tags"]:
                        if t in Tag: Tag[t] += 1
                        else: Tag[t] = 1
                    length_tag += len(d["tags"])
                else:
                    cnt += 1
                if "gid" in d and d["gid"]:
                    if d["gid"] not in coverage:
                        coverage[d["gid"]] = 1
                count += 1
            print("None_tag_num: {}, e_num:{} None_tag_num / numbers: {:.2f}".format(cnt, count - cnt, cnt / count))
            print("Data_Tags_Coverage:{:.2f} avg_length_tag:{:.2f}".format(len(coverage) / count, length_tag / (count - cnt)))
            T = sorted(Tag.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
            #num = sum([1 if v < 5 else 0 for k, v in T])
            #print(count, T, num, len(Tag), len(Tag)-num)
            #Td = {k:v for k,v in T if v >= 5}
            T = {k:v for k,v in T}
            print(T, count, len(T))
            print(set(self.knowledge.tags).difference(set([k for k,v in T.items()])))
            with open(os.path.join(self.database, "TagDict"), "w") as v:
                v.write(json.dumps(T, ensure_ascii="False"))


    def CreateTrainingData(self, tag):
        data = []
        root = os.path.join(self.database, tag)
        with open(os.path.join(self.database, "TagDict"), "r") as v:
            Tag = json.loads(v.readline().strip())
        # print(Tag)
        with open(os.path.join(root, "new_tags_data"), "r") as f:
            for line in f:
                d = json.loads(line.strip())
                if "tags" in d and d["tags"]:
                    if len(d["tags"]) == 1 and d["tags"][0] in Tag.keys():
                        data.append((d["content"], d["tags"]))
                    elif len(d["tags"]) > 1:
                        t = list(set(d["tags"]).intersection(set(Tag.keys())))
                        if len(t): data.append((d["content"], t))

        print("Remove unlabel data length: {}".format(len(data)))
        random.shuffle(data)
        train = int(len(data) / 10 * 9)
        dev = int(len(data) / 10 * 9.5)
        train_data = data[: train]
        dev_data = data[train: dev]
        test_data = data[dev:]
        print("length Train/Dev/Test {}:{}:{}".format(len(train_data), len(dev_data), len(test_data)))
        write_data(train_data, os.path.join(self.database, "text_train"),
                   os.path.join(self.database, "label_train"))
        write_data(dev_data, os.path.join(self.database, "text_val"),
                   os.path.join(self.database, "label_val"))
        write_data(test_data, os.path.join(self.database, "text_test"),
                   os.path.join(self.database, "label_test"))

    def sample_new_tags_data(self, tag):
        root = os.path.join(self.database, tag)
        data = []
        with open(os.path.join(root, "new_tags_data"), "r") as f:
            for line in f:
                di = json.loads(line.strip())
                if 0 < len(di["tags"]) <= 3 and "平昌冬奥会" in di["content"]:
                    data.append((di["content"], di["tags"]))
        dis = random.sample(data,  3)
        return [(unicodedata.normalize('NFKC', c), t)for c, t in dis]


if __name__ == "__main__":
    D = Database()
    #gids, max_gid = D.getPieceDataExample("新闻", start_time="2020-05-01         08:00:00", end_time="2020-5-30 21:00:00")
    # D.getOlympicData("新闻")
    # D.filterData("新闻")
    # D.getOlympicTag("新闻")
        # None_tag_num: 19350, e_num:107139 None_tag_num / numbers: 0.15
        # Data_Tags_Coverage:1.00 avg_length_tag:3.09
        # length Train/Dev/Test 96425:5357:5357
    D.CreateTrainingData("新闻")
    # print(D.sample_new_tags_data("新闻"))
    # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))



# PYTHONHASHSEED=1 python preprocess.py -data=AAPD

# python pretrain.py -config=aapd.yaml -gpuid=0 -train -test

# python classification.py -config=aapd.yaml -in=default -out=tuned -gpuid=0 -train -test

# python test_text.py -text="平昌冬奥会短道速滑" -config=aapd.yaml -in=default -out=tuned -gpuid=2

import os

class OlympicKnowledge(object):

    def __init__(self):
        self.Event = [
            "冬季两项(越野滑雪&射击)", # rules select
            "雪车(有舵雪橇)", "钢架雪车(俯式冰橇)",
            "冰壶", "冰球", "雪橇(无舵雪橇)", "花样滑冰", "短道速滑",
            "速度滑冰", "高山滑雪", "越野滑雪", "自由式滑雪",
            "北欧两项(跳台滑雪&越野滑雪)" # rules select
            "跳台滑雪", "单板滑雪"
        ]
        self.Stadium = {
            "北京": ["首都体育馆", "国家速滑馆", "国家体育馆", "五棵松体育中心", "国家游泳中心", "首钢滑雪大跳台中心"],
            "延庆": ["国家高山滑雪中心", "国家雪车雪橇中心"],
            "张家口": ["云顶滑雪公园", "国家跳台滑雪中心", "国家越野滑雪中心", "国家冬季两项中心"]
        }
        self.Organization = [
            "国际奥委会",
            "中国奥委会(国家体育总局)",
            "北京冬奥组委(北京2022年冬奥会和冬残奥会组织委员会)",
        ]
        self.Volunteer = [
            "前期志愿者项目",
            "测试赛志愿者项目",
            "赛会志愿者项目",
            "城市志愿者项目",
            "志愿服务遗产转化项目"
        ] # rules select
        self.Athletes = ["武大靖", "韩聪", "隋文静", "李靳宇", "周洋"]
        self.tags, self.tag_set = self.create_tagset()
        self.len_tags = len(self.tags)

    def create_tagset(self):
        tag, tag_set = list(), dict()
        tag += [e.split("(")[0] if "(" in e else e for e in self.Event]
        tag_set["Event"] = [e for e in self.Event]
        stadium = [value for _,v in self.Stadium.items() for value in v]
        tag.extend(stadium)
        tag_set["Stadium"] = stadium
        tag += [org.split("(")[0] if "(" in org else org for org in self.Organization]
        tag_set["Organization"] = [org for org in self.Organization]
        volunteer = [v for v in self.Volunteer]
        athletes = [a for a in self.Athletes]
        tag.extend(volunteer)
        tag_set["Volunteer"] = volunteer
        tag.extend(athletes)
        tag_set["Athletes"] = athletes
        return tag, tag_set

    def create_tages(self, text):
        # create model training samples, remove part of labels
        tags = self.get_tags(text)
        part_of_labels = self.Volunteer + ["冬季两项", "北欧两项"]
        return list(set(tags).difference(set(part_of_labels)))

    def get_tags(self, text):
        tags = list()
        for k, val in self.tag_set.items():
            for t in val:
                if "(" in t and "&" in t:
                    tl = t.split("(")[0]
                    tr = t.split("(")[-1].strip(")").split("&")
                    tr = [True for i in tr if i in text]
                    if tl in text or False not in tr:
                        tags.append(tl)
                if "(" in t and "&" not in t:
                    tl, tr = t.split("(")[0], t.split("(")[-1].strip(")")
                    tlr = [True for ti in [tl, tr] if ti in text]
                    if True in tlr:
                        tags.append(tl)
                else:
                    if t in text:
                        tags.append(t)
        return tags


if __name__ == "__main__":
     o = OlympicKnowledge()
     print(o.len_tags, o.tags, o.tag_set)





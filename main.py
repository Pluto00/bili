import threading
import requests
from Get_ip import IpPool
import random
import pymysql
import time


class GetInfo(object):  # 定义一个爬取类
    def __init__(self):
        # 爬虫开始的准备
        self.ip_pool = IpPool()  # 实例化一个IpPool类的对象，获得代理IP池
        self.headers = {  # 爬虫headers设置
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7',
            'Connection': 'keep-alive',
            'Host': 'api.bilibili.com',
            'Origin': 'https://www.bilibili.com',
        }
        self.URL_VIDinfo = "http://api.bilibili.com/archive_stat/stat?aid="  # b站视频信息api
        self.count = 0
        self.start_time = time.time()
        # 数据库准备
        self.db = pymysql.connect("localhost", "root", "", "bilibili", charset='utf8')  # 连接数据库
        self.cursor = self.db.cursor()  # 获得操作游标
        self.sql = """insert into video  
                    (aid, view, danmaku, reply, favorite, coin, share, awesome)
                    values(%s, %s, %s, %s, %s, %s, %s, %s)"""  # mysql插入语句

    def download(self, start, end):
        for video_id in range(start, end):
            try:  # 有的视频已经挂掉，拿不到数据
                video_list = []
                proxies = random.choice(self.ip_pool.ip_pool)  # 从ip池里面随机拿出一个ip
                response = requests.get(url=self.URL_VIDinfo + str(video_id), headers=self.headers,
                                        proxies=proxies).json()
                data = response['data']
                video_info = (
                    data['aid'], data['view'], data['danmaku'],
                    data['reply'], data['favorite'], data['coin'],
                    data['share'], data['like'])
                video_list.append(video_info)
            except:
                pass
                # print("AV:%09d 视频已不存在" % video_id)
            else:
                try:  # 执行写入数据库的语句
                    if mutex.acquire(True):
                        for row in video_list:
                            self.cursor.execute(self.sql, row)
                            # print(row)
                            self.count += 1
                    mutex.release()
                except Exception as e:
                    print(e)
                else:  # 降低爬虫速度，防止被禁
                    if self.count > 0 and self.count % 100 == 0:
                        print("爬取平均速度：%d 部/秒" % (self.count / (time.time() - self.start_time)))
                    time.sleep(1)


if __name__ == '__main__':
    for j in range(10):
        print("开始第 %d 轮循环爬取" % j)
        # 初始化获得ip
        video = GetInfo()  # 初始化爬取类
        print("开始爬取信息.....")
        # 设置多线程
        thread = []
        mutex = threading.Lock()  # 设置互斥锁，保护线程安全
        for i in range(j*10000, j*10000+10000, 1000):  # 设置爬虫起点和结束的av号，根据需求自己设置
            t = threading.Thread(target=video.download, args=(i, i + 1000))
            thread.append(t)
        for i in range(len(thread)):
            thread[i].start()
        for i in range(len(thread)):
            thread[i].join()

        # mysql操作
        video.cursor.close()  # 关闭游标
        video.db.commit()  # 提交之前的操作,否则数据不会插进去，是个巨坑
        video.db.close()  # 关闭数据库
        print("第 %d 轮循环功爬取 %d 部视频" % (j, video.count))
    print("程序结束~~~~~~")

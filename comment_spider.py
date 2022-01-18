#!/usr/bin/env python # -*- coding: utf-8 -*-

import requests
import os
import re
import csv
import time
import json


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0 weibo/1.2.1"
}
Cookies = {
    "Cookie": ""
}

output_dir = '/weibo'

class Weibo(object):
    # 用户信息，同时也能获取到uid、fid、oid等关键参数
    def usr_info(self, usr_id):
        time.sleep(2)
        url = (
            "https://m.weibo.cn/api/container/getIndex?type=uid&value={usr_id}".format(
                usr_id=usr_id
            )
        )
        resp = requests.get(url, headers=headers, cookies=Cookies)
        jsondata = resp.json().get("data")
        if jsondata.get("userInfo") == None:
            return {}
        nickname = jsondata.get("userInfo").get("screen_name")
        mblog_num = jsondata.get("userInfo").get("statuses_count")
        verified = jsondata.get("userInfo").get("verified")
        verified_reason = jsondata.get("userInfo").get("verified_reason")
        gender = jsondata.get("userInfo").get("gender")
        urank = jsondata.get("userInfo").get("urank")  # 用户等级
        mbrank = jsondata.get("userInfo").get("mbrank")
        followers_count = jsondata.get("userInfo").get("followers_count")
        follow_count = jsondata.get("userInfo").get("follow_count")
        containerid = jsondata.get("tabsInfo").get("tabs")[0].get("containerid")
        Info = {
            "uid": usr_id,
            "nickname": nickname,
            "mblog_num": mblog_num,
            "verified": verified,
            "verified_reason": verified_reason,
            "gender": gender,
            "urank": urank,
            "mbrank": mbrank,
            "followers_count": followers_count,
            "follow_count": follow_count,
            "containerid": containerid
        }
        return Info

    # 获取所有热门微博信息（所发微博内容，每条微博的评论id,转发数，评论数...）
    def mblog_list(self, uid, oid):
        Mblog_list = []
        base_url = "https://m.weibo.cn/api/container/getIndex?containerid={oid}&type=uid&value={uid}"
        page_url = "https://m.weibo.cn/api/container/getIndex?containerid={oid}&type=uid&value={uid}&page={page}"
        url = base_url.format(oid=oid, uid=uid)
        resp = requests.get(url, headers=headers, cookies=Cookies)
        resp.encoding = "gbk"
        response = resp.json()
        # 热门微博数total
        total = response["cardlistInfo"]["total"]
        # 热门微博网页数
        page_num = int(int(total) / 10) + 1
        for i in range(1, page_num + 1, 1):
            p_url = page_url.format(oid=oid, uid=uid, page=i)
            page_resp = requests.get(p_url, headers=headers, cookies=Cookies)
            page_data = page_resp.json()
            try:
                cards = page_data["cards"]
                for card in cards:
                    mblog = card["mblog"]
                    created_at = mblog["created_at"]
                    id = mblog["id"]
                    dirty_text = mblog["text"]  # dirty_text中含有很多链接杂质
                    cleaned1 = re.sub(r"<span .*?</span>", "", dirty_text)
                    text = re.sub(r"<a .*?</a>", "", cleaned1)
                    reposts_count = mblog["reposts_count"]
                    comments_count = mblog["comments_count"]
                    attitudes_count = mblog["attitudes_count"]
                    mblog_data = {
                        "created_at": created_at,
                        "id": id,
                        "text": text,
                        "reposts_count": reposts_count,
                        "comments_count": comments_count,
                        "attitudes_count": attitudes_count,
                    }
                    Mblog_list.append(mblog_data)
                    print(" " * 10, mblog_data)
            except:
                continue
            time.sleep(1)
        return Mblog_list

    # 获取某微博评论，保存到usr_id下的文件夹wb_id.csv文件中
    def get_comments(self, usr_id, wb_id):
        url = "https://m.weibo.cn/api/comments/show?id={id}".format(id=wb_id)
        page_url = "https://m.weibo.cn/api/comments/show?id={id}&page={page}"
        Resp = requests.get(url, headers=headers, cookies=Cookies)
        if Resp.json().get("data") == None:
            return 
        page_max_num = Resp.json()["data"]["max"]
        path = os.getcwd() + output_dir + "/{dirname}/".format(dirname=usr_id)
        if not os.path.exists(path):
          os.mkdir(path)
        path2 = os.getcwd() + output_dir +  "/%s/%s.csv" % (usr_id, wb_id)
        csvfile = open(path2, "a+", encoding="utf-8", newline="")
        writer = csv.writer(csvfile)
        writer.writerow(
            (
                "username",
                "verified",
                "verified_type",
                "profile_url",
                "source",
                "review_id",
                "like_counts",
                "image",
                "date",
                "comment",
            )
        )
        page = 1
        while page <= page_max_num:
            time.sleep(3)
            p_url = page_url.format(id=wb_id, page=page)
            resp = requests.get(p_url, cookies=Cookies, headers=headers)
            print("fetched page: {0}, status code: {1}".format(page, resp.status_code))
            
            if resp.status_code != 200:
                continue
            resp_data = resp.json()
            try:
                if resp_data.get("data") == None:
                    print(resp_data)
                    break
                data = resp_data.get("data").get("data")
                print(data)
                for d in data:
                    review_id = d["id"]
                    like_counts = d["like_counts"]
                    source = d["source"]
                    username = d["user"]["screen_name"]
                    image = d["user"]["profile_image_url"]
                    verified = d["user"]["verified"]
                    verified_type = d["user"]["verified_type"]
                    profile_url = d["user"]["profile_url"]
                    dirty_text = d["text"]
                    cleaned1 = re.sub(r"<span .*?</span>", "", dirty_text)
                    comment = re.sub(r"<a .*?</a>", "", cleaned1)
                    date = d["created_at"]
                    print(comment)
                    writer.writerow(
                        (
                            username,
                            verified,
                            verified_type,
                            profile_url,
                            source,
                            review_id,
                            like_counts,
                            image,
                            date,
                            comment,
                        )
                    )
                print("有%d页，已经爬了%d页   %s" % (page_max_num, page, comment))
                page += 1
            except:
                print(resp_data)
                print(resp_data["msg"])
                continue
        csvfile.close()
    # 读取文件，获取所有帖子评论
    def get_comments_by_list(self, file = "user_list.txt"):
        with open(file, "r") as f:
            for line in f.readlines():
                line = line.strip('\n').split('/')
                print(line)
                wb.get_comments(*line)
    # 读取文件，获取所有用户信息
    def get_usr_info_by_list(self, file = "user_id_list.txt"):
        path = os.getcwd() + output_dir +  "/userinfo.csv"
        csvfile = open(path, "a+", encoding="utf-8", newline="")
        writer = csv.writer(csvfile)
        if len(csvfile.readlines()) < 1:
            writer.writerow(
                (
                    "uid",
                    "nickname",
                    "mblog_num",
                    "verified",
                    "verified_reason",
                    "gender",
                    "urank",
                    "mbrank",
                    "followers_count",
                    "follow_count",
                    "containerid"
                )
            )
        with open(file, "r") as f:
            for line in f.readlines():
                line = line.strip('\n')
                print(line)
                info = wb.usr_info(line)
                print(info)
                if info.get("uid") == None:
                    continue
                writer.writerow(
                        (
                            info["uid"],
                            info["nickname"],
                            info["mblog_num"],
                            info["verified"],
                            info["verified_reason"],
                            info["gender"],
                            info["urank"],
                            info["mbrank"],
                            info["followers_count"],
                            info["follow_count"],
                            info["containerid"]
                        )
                    )
        csvfile.close()
wb = Weibo()

path = os.getcwd() + output_dir
if not os.path.exists(path):
          os.mkdir(path)

wb.get_usr_info_by_list()


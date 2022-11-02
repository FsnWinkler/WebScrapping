from collections import Counter
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import pandas as pd
import pymongo
from datetime import datetime
from pyyoutube import Api
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import re
import json
import makeClip
from scenedetect import open_video, ContentDetector, SceneManager, StatsManager
import pandas as pd
from pytube import YouTube
from pytube.cli import on_progress
import threading


def Scrap_Trends_for_URLS():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument("--headless")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--force-dark-mode")
    driver = webdriver.Chrome('./chromedriver', options=options)  # options=options
    driver.get("https://www.youtube.com/feed/explore")
    time.sleep(2)
    button = driver.find_element(By.XPATH,
                                 "/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/form[2]/div/div/button")
    time.sleep(2)
    button.click()
    prev_h = 0
    while True:
        height = driver.execute_script("""
                function getActualHeight() {
                    return Math.max(
                        Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
                        Math.max(document.body.offsetHeight, document.documentElement.offsetHeight),
                        Math.max(document.body.clientHeight, document.documentElement.clientHeight)
                    );
                }
                return getActualHeight();
            """)
        driver.execute_script(f"window.scrollTo({prev_h},{prev_h + 200})")
        # fix the time sleep value according to your network connection
        time.sleep(1)
        prev_h += 200
        print(prev_h)

        if prev_h >= height:  # 6000 for top coments
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    all_hrefs = []

    for a in soup.find_all('a', href=True):
        all_hrefs.append(a["href"])
    urls = list(set([i for i in all_hrefs if i.__contains__("watch")]))
    for y in range(len(urls)):
        print("Found the URL: " + str(urls[y]))
    driver.quit()
    return urls


def connenct_db():
    i = 0
    while i < 50:
        try:
            load_dotenv()
            cluster = pymongo.MongoClient(

                os.getenv("db_key"))
            db = cluster["test"]
            return db
        except:
            time.sleep(20)
            i += 1


def insert_db(data, col):
    db = connenct_db()

    if col == "comments":
        collection = db[col]
        for i in range(len(data)):
            if collection.find_one({"Comment": data["Comment"].iloc[i]}):
                dataset = collection.find_one({"Comment": data["Comment"].iloc[i]})
                if dataset.get("Likes") < data["Likes"].iloc[i].item():
                    newvalues = {"$set": {"Likes": data["Likes"].iloc[i].item()}}
                    collection.update_one(dataset, newvalues)
                    print("succsessfully  updated {} to {}  into database".format(dataset, newvalues))
                else:
                    print("Likes are up to date!")

            else:
                # record_to_insert = data.loc[i].to_dict("list")
                collection.insert_one(data.iloc[i].to_dict())
                print("succsessfully inserted {}  into database".format(data.iloc[i]))

    if col == "mostcommon":
        collection = db[col]
        if collection.find_one({"URL": data["URL"]}):
            print("already got most common words")
        else:
            collection.insert_one(data)
            print("succsessfully inserted {}  into database".format(data))

    if col == "timestamps":
        collection = db[col]
        try:
            for i in range(len(data)):
                if collection.find_one({"Comment": data["Comment"].iloc[i]}):
                    print("Timestamp is uptodate")
                    continue

                else:
                    # record_to_insert = data.loc[i].to_dict("list")
                    collection.insert_one(data.iloc[i].to_dict())
                    print("succsessfully inserted {}  into database".format(data.iloc[i]))

        # try:
        #     collection.insert_many(data.to_dict("records"))
        #     print("succsessfully inserted timestamps")
        except:
            print("no timestamps")

    print("")


def find_most_common_words(all_words):
    f = open("C:\\Users\\ffff\\PycharmProjects\\WebScrapping\\stopwords-de-master\\stopwords-de.json", encoding="utf8")
    ger_data = json.load(f)
    f.close()

    f = open("C:\\Users\\ffff\\PycharmProjects\\WebScrapping\\stopwords-en-master\\stopwords-en.json", encoding="utf8")
    eng_data = json.load(f)
    f.close()

    counts = dict()
    for x in all_words:
        words = x.lower().split()
        for word in words:
            if word in eng_data or word in ger_data:
                continue
            else:
                if word in counts:
                    counts[word] += 1
                else:
                    counts[word] = 1

    most_common = dict(Counter(counts).most_common(10))
    return most_common


def ScrapComment(url):
    url_id = url[32:43]
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument("--headless")
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument("--start-maximized")
    driver = webdriver.Chrome('./chromedriver', options=options)

    driver.get("https://www.youtube.com/watch?v=NLXGrLpJ2dQ")
    cookies_path = 'cookie'

    with open(cookies_path, 'r') as file_path:
        cookies_list = json.loads(file_path.read())

    # Once on that domain, start adding cookies into the browser
    for cookie in cookies_list:
        # If domain is left in, then in the browser domain gets transformed to f'.{domain}'
        cookie.pop('domain', None)
        driver.add_cookie(cookie)
        print("cookies loaded")
    time.sleep(5)
    driver.maximize_window()
    driver.get(url)
    start_time = datetime.now()
    driver.set_window_size(1280, 800)
    prev_h = 0
    while True:
        height = driver.execute_script("""
                function getActualHeight() {
                    return Math.max(
                        Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
                        Math.max(document.body.offsetHeight, document.documentElement.offsetHeight),
                        Math.max(document.body.clientHeight, document.documentElement.clientHeight)
                    );
                }
                return getActualHeight();
            """)
        driver.execute_script(f"window.scrollTo({prev_h},{prev_h + 200})")
        # fix the time sleep value according to your network connection
        time.sleep(1)
        prev_h += 400
        print(prev_h)

        if prev_h >= height:  # 6000 for top coments
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')



    comment_div = soup.select("#content #content-text")  # limit=50 for only top comments
    comment_div_array = [x.text for x in comment_div]


    title_text_div = soup.select_one('#container h1')
    title = title_text_div and title_text_div.text
    most_common = find_most_common_words(comment_div_array)
    most_common["URL"] = url
    most_common["Title"] = title
    insert_db(most_common, "mostcommon")

    # -------------------------make $screenshots of timestamp comments-------------------------------
    counter_array = []
    time_array = []
    i = 0
    for item in comment_div_array:
        timestamp = re.findall("[0-9]+[0-9]+[:]+[0-9]+[0-9]" and "[0-9]+[:]+[0-9]+[0-9]", item)
        if timestamp:
            if len(time_array) == 0:
                first_comment = driver.find_element(By.XPATH,
                                                    "//*[@id='contents']/ytd-comment-thread-renderer[1]")
                if not os.path.exists(os.getcwd() + "\\screenshots_of_comments\\{}".format(url_id)):
                    os.makedirs(os.getcwd() + "\\screenshots_of_comments\\{}".format(url_id))
                first_comment.screenshot(os.getcwd() + "\\screenshots_of_comments\\{}\\first.png".format(url_id))
            time_array.append(comment_div_array[i])
            comment = driver.find_element(By.XPATH, "//*[@id='contents']/ytd-comment-thread-renderer[{}]".format(i + 1))

            time.sleep(2)
            if not os.path.exists(os.getcwd() + "\\screenshots_of_comments\\{}".format(url_id)):
                os.makedirs(os.getcwd() + "\\screenshots_of_comments\\{}".format(url_id))
            comment.screenshot(os.getcwd() + "\\screenshots_of_comments\\{}\\screen_{}.png".format(url_id, i + 1))
            counter_array.append(int(i + 1))
            print("screenshot saved")
            i += 1
        else:
            counter_array.append(None)
            i += 1

    driver.quit()

    # -------------------------make $timestamp array-------------------------------
    timestamp_as_secounds = []
    # time_as_no_Nones = [i for i in timestamp_as_secounds if i is not None]
    # print(time_as_no_Nones)
    timestamp_array = []
    # time_no_Nones = [i for i in timestamp_array if i is not None]
    # print(time_no_Nones)
    for item in comment_div_array:
        timestamp = re.findall("[0-9]+[0-9]+[:]+[0-9]+[0-9]" and "[0-9]+[:]+[0-9]+[0-9]", item)
        if timestamp:
            if len(timestamp[0]) == 4:
                to_add = "0"
                res = "".join((to_add, timestamp[0]))
            elif len(timestamp[0]) == 7:
                to_add = "0"
                res = "".join((to_add, timestamp[0]))
            else:
                res = timestamp[0]
            timestamp_array.append(res)
        else:
            timestamp_array.append(None)

    for i in range(len(timestamp_array)):
        timestamp = timestamp_array[i]
        if timestamp == None:
             timestamp_as_secounds.append(None)
        elif len(timestamp) == 5:
            as_secounds = int(timestamp[0:2]) * 60 + int(timestamp[3:5])
            timestamp_as_secounds.append(as_secounds)
        elif len(timestamp) == 8:
            as_secounds = int(timestamp[0:2]) * 60 + int(timestamp[3:5]) + int(timestamp[6:8])
            timestamp_as_secounds.append(as_secounds)
        else:
            timestamp_as_secounds.append(None)

    # -------------------------make $like array-------------------------------
    like_div = soup.select("#toolbar #vote-count-left")
    like_div_stripped = []
    for item in like_div:
        new_item = item.get_text().replace("\n", "")
        final_item = new_item.replace(" ", "")
        like_div_stripped.append(int(final_item))

    # -------------------------make $author array-------------------------------
    author_div = soup.select("#header-author #author-text")
    author_div_stripped = []
    for item in author_div:
        new_item = item.get_text().replace("\n", "")
        final_item = new_item.replace(" ", "")
        author_div_stripped.append(str(final_item))

    download_yt_video(url)

    # -------------------------make $start and endtime arrays-------------------------------
    begin_of_scenes = find_scenes(os.getcwd() + "\Videos\{}.mp4".format(url[32:43]))
    start_times = []
    start_no_Nones  = [i for i in start_times if i is not None]
    end_times = []
    end_no_Nones = [i for i in end_times if i is not None]
    try:
        for i in range(len(timestamp_as_secounds)):
            if timestamp_as_secounds[i] == None:
                start_times.append(None)
                end_times.append(None)
                continue
            for y in range(len(begin_of_scenes)):
                if timestamp_as_secounds[i] < begin_of_scenes[y]:
                    if (begin_of_scenes[y] - timestamp_as_secounds[i]) > 8 and (begin_of_scenes[y] - timestamp_as_secounds[i]) < 30:
                        start_times.append(int(timestamp_as_secounds[i]))
                        end_times.append(int(begin_of_scenes[y]))
                        break
                if y + 1 == len(begin_of_scenes):
                    start_times.append(int(timestamp_as_secounds[i]))
                    end_times.append(int(timestamp_as_secounds[i] + 15))

    except:
        print("get start and endtime error")


    data = pd.DataFrame(
        { "URL": url, "Comment": comment_div_array, "Author": author_div_stripped, "Likes": like_div_stripped,
         "Timestamp": timestamp_array, "Counter": counter_array, "Starttime": start_times, "Endtime": end_times})
    # print(data)
    insert_db(data, "comments")
    sorted_data = data.sort_values(by="Likes", ascending=False)
    # print(sorted_data[0:10])

    # timestamp_df = data.loc[data['Timestamp'].notnull()]
    #
    # end_time = datetime.now()
    # print(end_time - start_time)
    #
    # np_array = sorted_data[0:10].to_numpy()
    # dataframe_sorted = pd.DataFrame(np_array,
    #                                 columns=['Likes', 'Comment', 'Author', 'URL', 'Title', 'Timestamp', 'Counter'])

    # insert_db(timestamp_df, "timestamps")
    # insert_db(dataframe_sorted, "comments")
    # print(sorted_data.to_json())
    # print(sorted_data.to_dict("records"))
    # print(sorted_data.to_dict("index"))

    # print(title, comment_list, like_list)
    # print(len(comment_list))

def download_yt_video(url):
    try:
        if os.path.exists(os.getcwd()+"\Videos" + url[32:43] + ".mp4"):
            print("Video already exists")
            pass
        else:
            yt = YouTube(url, on_progress_callback=on_progress)
            stream = yt.streams.get_highest_resolution()
            print(stream.filesize_approx)
            stream.download(os.getcwd()+"\Videos", filename=url[32:43] + ".mp4")
            print('Download Completed!' + stream.title)

            #if os.path.exists(os.getcwd()+"\Videos" + url[32:43] + ".mp4"):



    except:
        print("download error")

# def get_startTime_and_endTime(url):
#     load_dotenv()
#     cluster = pymongo.MongoClient(
#         os.getenv("db_key"))
#     db = cluster["test"]
#     collection = db["timestamps"]
#     # pymongo_cursor = collection.find({})
#     all_data = [document for document in collection.find({"URL": "{}".format(url)})]
#     if all_data == None:
#         print("no entrys found in db")
#
#     comment_arr = []
#     author_arr = []
#     URL_arr = []
#     timestamp_arr = []
#     counter_arr = []
#     likes_arr = []
#
#     for i in range(len(all_data)):
#         comment = all_data[i]["Comment"]
#         comment = re.sub('\d+\d+:+\d+\d', '', comment)
#         comment = re.sub('\d+:+\d+\d', '', comment)
#         comment_arr.append(comment)
#         author_arr.append(all_data[i]["Author"])
#         URL_arr.append(all_data[i]["URL"])
#         counter_arr.append(int(all_data[i]["Counter"]))
#
#         # if len(all_data[i]["Timestamp"]) == 4:  # add a 0 if start_time string 0:00 format 00:00 required
#         #     to_add = "0"
#         #     res = "".join((to_add, all_data[i]["Timestamp"]))
#         # else:
#         #     res = all_data[i]["Timestamp"]
#
#         likes_arr.append(all_data[i]["Likes"])
#
#     comment_author_url_timestamp_df = pd.DataFrame(
#         {"Comment": comment_arr, "Author": author_arr, "URL": URL_arr, "Timestamp": timestamp_arr})
#     # filtered_df = comment_author_url_timestamp_df.loc[comment_author_url_timestamp_df["URL"] == url]
#     times_df = comment_author_url_timestamp_df["Timestamp"].dropna(
#         0)  # .where(comment_author_url_timestamp_df["URL"] == "https://www.youtube.com/watch?v=QPJH4d8s1yM")
#     # sorted_times_df  = times_df.sort_values(by="Likes", ascending=False)
#     # timestamps = []
#     # try:
#     #     for i in range(len(times_df)):
#     #         timestamp = times_df.loc[i]
#     #         as_secounds = int(timestamp[0:2]) * 60 + int(timestamp[3:5])
#     #         timestamps.append(as_secounds)
#     # except:
#     #     print("error")
#
#     # begin_of_scenes = find_scenes(os.getcwd() + "\Videos\{}.mp4".format(url[32:43]))
#     # start_and_endtime = {"Starttime": [], "Endtime": []}
#
#     # for i in range(len(timestamps)):
#     #     for y in range(len(begin_of_scenes)):
#     #         if timestamps[i] <= begin_of_scenes[y]+10 and timestamps[i] <= begin_of_scenes[y]+15:
#     #             if timestamps[i]-begin_of_scenes[y] <= 10:
#     #                 start_and_endtime["Starttime"].append(timestamps[i])
#     #                 start_and_endtime["Endtime"].append(begin_of_scenes[y])
#     #             start_and_endtime["Starttime"].append(timestamps[i])
#     #             start_and_endtime["Endtime"].append(begin_of_scenes[y])
#     #             break
#     #         elif y ==len(begin_of_scenes):
#     #             start_and_endtime["Starttime"].append(timestamps[i])
#     #             start_and_endtime["Endtime"].append(timestamps[i]+15)
#     # try:
#     #     for i in range(len(timestamps)):
#     #         for y in range(len(begin_of_scenes)):
#     #             if timestamps[i] < begin_of_scenes[y]:
#     #                 if (begin_of_scenes[y] - timestamps[i]) > 8 and (begin_of_scenes[y] - timestamps[i]) < 30:
#     #                     start_and_endtime["Starttime"].append(timestamps[i])
#     #                     start_and_endtime["Endtime"].append(begin_of_scenes[y])
#     #                     break
#     #             if y + 1 == len(begin_of_scenes):
#     #                 start_and_endtime["Starttime"].append(timestamps[i])
#     #                 start_and_endtime["Endtime"].append(timestamps[i] + 15)
#     # except:
#     #     print("error 2")
#     #
#     # liste = []
#     # try:
#     #     for i in range(len(timestamps)):
#     #         liste.append(start_and_endtime["Endtime"][i] - start_and_endtime["Starttime"][i])
#     # except:
#     #     print("timestamp error")
#     print(liste)
#     final_df = pd.DataFrame(
#         {"Comment": comment_arr, "Author": author_arr, "URL": URL_arr, "Starttime": start_and_endtime["Starttime"],
#          "Endtime": start_and_endtime["Endtime"], "Counter": counter_arr, "Likes": likes_arr})
#     sorted_final_df = final_df.sort_values(by="Likes", ascending=False)
#     print("")
#
#     load_dotenv()
#     cluster = pymongo.MongoClient(os.getenv("db_key"))
#     db = cluster["test"]
#
#     collection = db["final_timestamps"]
#     for i in range(len(sorted_final_df)):
#         if collection.find_one({"Comment": sorted_final_df["Comment"].iloc[i]}):
#             continue
#             # dataset = collection.find_one({"Comment": final_df["Comment"].iloc[i]})
#             # if dataset.get("Likes") < final_df["Likes"].iloc[i]:
#             #     newvalues = {"$set": {"Likes": final_df["Likes"].iloc[i]}}
#             #     collection.update_one(dataset, newvalues)
#             #     print("succsessfully  updated {} to {}  into database".format(dataset, newvalues))
#             # else:
#             #     print("Likes are up to date!")
#
#         else:
#             # record_to_insert = data.loc[i].to_dict("list")
#             collection.insert_one(sorted_final_df.iloc[i].to_dict())
#             print("succsessfully inserted {}  into database".format(final_df.iloc[i]))


def find_scenes(video_path):
    video_stream = open_video(video_path)
    stats_manager = StatsManager()
    # Construct our SceneManager and pass it our StatsManager.
    scene_manager = SceneManager(stats_manager)

    # Add ContentDetector algorithm (each detector's constructor
    # takes various options, e.g. threshold).
    scene_manager.add_detector(ContentDetector(threshold=55.0))

    # Save calculated metrics for each frame to {VIDEO_PATH}.stats.csv.
    stats_file_path = '%s.stats.csv' % video_path

    # Perform scene detection.
    scene_manager.detect_scenes(video=video_stream, show_progress=True)
    scene_list = scene_manager.get_scene_list()
    # for i, scene in enumerate(scene_list):
    #     print(
    #         'Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
    #         i+1,
    #         scene[0].get_timecode(), scene[0].get_frames(),
    #         scene[1].get_timecode(), scene[1].get_frames(),))

    begin_of_scenes = []
    for i in range(len(scene_list)):
        as_timecode = str(scene_list[i][0])[3:8]
        as_secounds = int(as_timecode[0:2]) * 60 + int(as_timecode[3:5])

        begin_of_scenes.append(as_secounds)

    return begin_of_scenes


def get_youtube_urls():
    load_dotenv()
    api_key = os.getenv("api_key")
    # youtube = build('youtube', 'v3', developerKey=api_key)
    api = Api(api_key=api_key)

    video_by_chart = api.get_videos_by_chart(chart="mostPopular", region_code="de", count=10, category_id="22")
    ID = []
    # category list of IDs
    # 1 - Film & Animation
    # 2 - Autos & Vehicles
    # 10 - Music
    # 15 - Pets & Animals
    # 17 - Sports
    # 18 - Short
    # 19 - Travel & Events
    # 20 - Gaming
    # 21 - Videoblogging
    # 22 - People & Blogs
    # 23 - Comedy
    # 24 - Entertainment
    # 25 - News & Politics
    # 26 - Howto & Style
    # 27 - Education
    # 28 - Science & Technology
    # 29 - Nonprofits & Activism
    # 30 - Movies
    # 31 - Anime / Animation
    # 32 - Action / Adventure
    # 33 - Classics
    # 34 - Comedy
    # 35 - Documentary
    # 36 - Drama
    # 37 - Family
    # 38 - Foreign
    # 39 - Horror
    # 40 - Sci - Fi / Fantasy
    # 41 - Thriller
    # 42 - Shorts
    # 43 - Shows
    # 44 - Trailers
    for i in video_by_chart.items:
        # print(i.id)
        ID.append(i.id)
    return ID


def check_url(url):
    if os.path.exists("urls.json"):
        with open("urls.json", "r") as file:
            if url in file.read():
                print("url exists")
                return False
            else:
                return True
    else:
        with open("urls.json", "w") as file:
            file.write(url)


def write_url(url):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    with open("urls.json", "a") as file:
        file.write("\n" + current_time + " " + url)


def main(url):
    # try:
    if check_url(url):
        ScrapComment(url)
        time.sleep(5)
        makeClip.main(url)
        write_url(url)
    else:
        pass

    # except:
    #     print("makeclip error")
    print("")


if __name__ == "__main__":
    # load_dotenv()
    # print(get_youtube_urls())
    # for i in range(len(get_youtube_urls())):
    #     main("https://www.youtube.com/watch?v={}".format(get_youtube_urls()[i]))
    # urls = Scrap_Trends_for_URLS()
    # for i in range(len(urls)):
    #     main("https://www.youtube.com{}".format(urls[i]))
    main("https://www.youtube.com/watch?v=3Q3c4E9COXs")

    # for i in range(0,5):
    #     ScrapComment("https://www.youtube.com/watch?v={}".format(ID[i]))

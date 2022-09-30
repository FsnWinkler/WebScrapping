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





def connect_db(sorted_data):
    cluster = pymongo.MongoClient(
        #"mongodb+srv://admin:JyggcLIE4DGsQtu8@cluster0.0lwnskf.mongodb.net/?retryWrites=true&w=majority")
        os.getenv("db_key"))
    db = cluster["test"]
    print(db.list_collection_names())
    isInList = False#url[32:] in db.list_collection_names()

    print(isInList)
    if isInList:
        print("record already here!")
    else:
        collection = db["timestamp"]
        collection.insert_many(sorted_data.to_dict("records"))
        print("succsessfully inserted  into database")


def ScrapComment(url):
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument("--headless")
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome('./chromedriver', options=options)
    driver.get(url)
    start_time = datetime.now()
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
        prev_h +=200
        print(prev_h)

        if prev_h >= 6000: #6000 for top coments
            break


    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    title_text_div = soup.select_one('#container h1')
    title = title_text_div and title_text_div.text


    comment_div = soup.select("#content #content-text") #limit=50 for only top comments
    like_div = soup.select("#toolbar #vote-count-left")
    author_div = soup.select("#header-author #author-text")

    timestamp_array = []
    comment_div_array = [x.text for x in comment_div]
    for item in comment_div_array:
        timestamp = re.findall("[0-9]+[0-9]+[:]+[0-9]+[0-9]" and "[0-9]+[:]+[0-9]+[0-9]", item)
        if timestamp:
            timestamp_array.append(timestamp[0])
        else:
            timestamp_array.append(None)




    like_div_stripped = []
    author_div_stripped = []
    for item in like_div:
        new_item = item.get_text().replace("\n", "")
        final_item = new_item.replace(" ", "")
        like_div_stripped.append(float(final_item))

    for item in author_div:
        new_item = item.get_text().replace("\n", "")
        final_item = new_item.replace(" ", "")
        author_div_stripped.append(str(final_item))

    data = pd.DataFrame({"Likes": like_div_stripped, "Comment": comment_div_array, "Author": author_div_stripped, "URL": url, "Title": title, "Timestamp": timestamp_array})
    #print(data)

    sorted_data = data.sort_values(by="Likes", ascending=False)
    #print(sorted_data[0:10])

    timestamp_df = data.loc[data['Timestamp'].notnull()]

    end_time = datetime.now()
    print(end_time - start_time)


    connect_db(timestamp_df)
    # print(sorted_data.to_json())
    # print(sorted_data.to_dict("records"))
    # print(sorted_data.to_dict("index"))





    # print(title, comment_list, like_list)
    # print(len(comment_list))





if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("api_key")


    youtube = build('youtube', 'v3', developerKey=api_key)
    api = Api(api_key=api_key)
    print(api.get_i18n_regions())

    video_by_chart = api.get_videos_by_chart(chart="mostPopular", region_code="de", count=5, category_id="24")
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
        print(i.id)
        ID.append(i.id)
    ScrapComment("https://www.youtube.com/watch?v=BDbWpN80PT4")#.format(ID[0])



    # for i in range(0,5):
    #     ScrapComment("https://www.youtube.com/watch?v={}".format(ID[i]))
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





def connect_db(data, col):
    load_dotenv()
    cluster = pymongo.MongoClient(

        os.getenv("db_key"))
    db = cluster["test"]


    if col == "comments":
        collection = db[col]
        for i in range(len(data)):
            if collection.find_one({"Comment": data["Comment"].iloc[i]}):
                dataset = collection.find_one({"Comment": data["Comment"].iloc[i]})
                if dataset.get("Likes") < data["Likes"].iloc[i]:
                    newvalues = { "$set": {"Likes": data["Likes"].iloc[i]}}
                    collection.update_one(dataset, newvalues)
                    print("succsessfully  updated {} to {}  into database".format(dataset, newvalues))
                else:
                    print("Likes are up to date!")

            else:
                #record_to_insert = data.loc[i].to_dict("list")
                collection.insert_one(data.loc[i].to_dict())
                print("succsessfully inserted {}  into database".format(data.loc[i]))
    if col == "timestamps":
        collection = db[col]
        try:
            for i in range(len(data)):
                if collection.find_one({"Comment": data["Comment"].iloc[i]}):
                    print("Timestamp is uptodate")
                    continue

                else:
                    #record_to_insert = data.loc[i].to_dict("list")
                    collection.insert_one(data.loc[i].to_dict())
                    print("succsessfully inserted {}  into database".format(data.loc[i]))

        # try:
        #     collection.insert_many(data.to_dict("records"))
        #     print("succsessfully inserted timestamps")
        except:
            print("no timestamps")

    print("")



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

        if prev_h >= height: #6000 for top coments
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

    np_array = sorted_data[0:11].to_numpy()
    dataframe_sorted = pd.DataFrame(np_array, columns=['Likes', 'Comment', 'Author', 'URL', 'Title', 'Timestamp'])

    connect_db(timestamp_df, "timestamps")
    connect_db(dataframe_sorted, "comments")
    # print(sorted_data.to_json())
    # print(sorted_data.to_dict("records"))
    # print(sorted_data.to_dict("index"))





    # print(title, comment_list, like_list)
    # print(len(comment_list))


def get_youtube_urls():

    api_key = os.getenv("api_key")
    #youtube = build('youtube', 'v3', developerKey=api_key)
    api = Api(api_key=api_key)

    video_by_chart = api.get_videos_by_chart(chart="mostPopular", region_code="de", count=10, category_id="23")
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
        #print(i.id)
        ID.append(i.id)
    return ID


if __name__ == "__main__":
    #load_dotenv()
    # print(get_youtube_urls())
    # for i in range(len(get_youtube_urls())):
    #     ScrapComment("https://www.youtube.com/watch?v={}".format(get_youtube_urls()[i]))
    ScrapComment("https://www.youtube.com/watch?v=BDbWpN80PT4")




    # for i in range(0,5):
    #     ScrapComment("https://www.youtube.com/watch?v={}".format(ID[i]))
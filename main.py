from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import pandas as pd
import pymongo
from datetime import datetime
from pyyoutube import Api
from apiclient.discovery import build



def connect_db(sorted_data):
    cluster = pymongo.MongoClient(
        "mongodb+srv://admin:JyggcLIE4DGsQtu8@cluster0.0lwnskf.mongodb.net/?retryWrites=true&w=majority")
    db = cluster["test"]
    print(db.list_collection_names())
    isInList = False#url[32:] in db.list_collection_names()

    print(isInList)
    if isInList:
        print("record already here!")
    else:
        collection = db["comments"]
        collection.insert_many(sorted_data.to_dict("records")[:10])
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

        if prev_h >= 6000:
            break


    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    title_text_div = soup.select_one('#container h1')
    title = title_text_div and title_text_div.text


    comment_div = soup.select("#content #content-text", limit=50)
    like_div = soup.select("#toolbar #vote-count-left", limit=50)
    author_div = soup.select("#header-author #author-text", limit=50)


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

    data = pd.DataFrame({"Likes": like_div_stripped, "Comment": [x.text for x in comment_div], "Author": author_div_stripped, "URL": url, "Title": title})
    #print(data)

    sorted_data = data.sort_values(by="Likes", ascending=False)
    #print(sorted_data[0:10])

    end_time = datetime.now()
    print(end_time - start_time)


    connect_db(sorted_data)
    # print(sorted_data.to_json())
    # print(sorted_data.to_dict("records"))
    # print(sorted_data.to_dict("index"))





    # print(title, comment_list, like_list)
    # print(len(comment_list))





if __name__ == "__main__":
    api_key = "AIzaSyBR6ynnF9j7DF1vhgJB04gyOOx4JYthMBg"  # Replace this dummy api key with your own.

    youtube = build('youtube', 'v3', developerKey=api_key)
    api = Api(api_key=api_key)

    video_by_chart = api.get_videos_by_chart(chart="mostPopular", region_code="DE", count=5, category_id="23")
    ID = []
    # print(video_by_chart.items)
    for i in video_by_chart.items:
        print(i.id)
        ID.append(i.id)
    #connect_db("https://www.youtube.com/watch?v={}".format(ID[0]))



    for i in range(0,5):
        ScrapComment("https://www.youtube.com/watch?v={}".format(ID[i]))
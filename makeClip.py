import shutil
import subprocess
import webbrowser
import json
import msal
from msal import PublicClientApplication
import requests
from dotenv import load_dotenv
import os
import pymongo
import cv2
import moviepy.editor as mp
import re
from moviepy.editor import VideoFileClip
import time
from datetime import datetime
import os.path


def cut_video(url):
    load_dotenv()
    cluster = pymongo.MongoClient(
        os.getenv("DB_KEY"))
    db = cluster["test"]
    collection = db["timestamp_comments"]
    all_data = [document for document in collection.find({"URL": url})]
    if all_data == None:
        print("no entrys found in db")
    duration = get_length(os.getcwd()+f"\Videos\{url[32:43]}.mp4")
    sorted_data = sorted(all_data, key=lambda d: d['Likes'], reverse=True)
    if len(sorted_data) > 6:
        runs = 5
    else:
        runs = len(sorted_data)
    for i in range(runs):
        if sorted_data[i]["Starttime"] > round(duration)-1:
            continue

        else:
            clip = VideoFileClip(os.getcwd()+f"\Videos\{sorted_data[i]['URL'][32:43]}.mp4").subclip(int(sorted_data[i]["Starttime"]), int(sorted_data[i]["Endtime"]))
            clip.to_videofile(os.getcwd()+f"\Clips\clip_{sorted_data[i]['URL'][32:43]}_{int(sorted_data[i]['Counter'])}.mp4", codec="libx264", temp_audiofile='temp-audio.m4a', remove_temp=True, audio_codec='aac')
            clip.close()
            time.sleep(2)
            add_screen_to_clip(sorted_data[i]["URL"][32:43], int(sorted_data[i]["Counter"]), i, sorted_data[i]["Timestamp"])
            print("final clip done")


def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)


def insert_db(src_link, url, counter):
    load_dotenv()
    cluster = pymongo.MongoClient(
        os.getenv("DB_KEY"))
    db = cluster["test"]
    print("connected to DB")
    collection = db["timestamp_comments"]
    collection.update_one({"$and": [{"URL": "https://www.youtube.com/watch?v=" + url}, {"Counter": counter}]}, {"$set": {"src_link": str(src_link)}})
    print(f"sucssesfully inserted {src_link} into db")


def add_screen_to_clip(url, counter, i, timestamp):
    video = mp.VideoFileClip(os.getcwd()+f"\Clips\clip_{url}_{counter}.mp4")

    logo = (mp.ImageClip(os.getcwd()+f"\screenshots_of_comments\{url}\screen_{counter}.png")
              .set_opacity(0.8)
              .set_duration(video.duration)
              #.resize(width=video.w-100) # if you need to resize...
              .margin(left=10, bottom=10, opacity=0) # (optional) logo-border padding
              .set_pos(("center", "bottom")))
    final = mp.CompositeVideoClip([video, logo])
    load_dotenv()
    PATH = os.getenv("VIDEO_PATH")
    if not os.path.exists(PATH+rf"\Clips_Final\Trends\{url}"):
        os.makedirs(PATH+r"\Clips_Final\Trends\{}".format(url))

    if not os.path.exists(PATH+r"\Clips_Final\Most_Liked_Clips"):
        os.makedirs(PATH+r"\Clips_Final\Most_Liked_Clips")


    if i == 0:
        clipname = PATH + rf"\Clips_Final\Most_Liked_Clips\clip_{url}.mp4"
        final.write_videofile(clipname, fps=60, codec="libx264")
        folder_id = os.getenv("FOLDER_ID_MOST_LIKED")
        src_link = upload_to_onedrive(clipname, f"https://www.youtube.com/watch?v={url}", timestamp, folder_id)
        insert_db(src_link, url, counter)
    else:
        clipname = PATH + rf"\Clips_Final\Trends\clip_{url}_{counter}.mp4"
        final.write_videofile(clipname, fps=60, codec="libx264")
        folder_id = os.getenv("FOLDER_ID_CLIPS")
        src_link = upload_to_onedrive(clipname, f"https://www.youtube.com/watch?v={url}", timestamp, folder_id)
        insert_db(src_link, url, counter)


    print(f"*********{src_link}*********")
    # INSERT DB SRC LINK
    write_url(clipname[33:])
    print("sucsessfully created clip: " + clipname)

def generate_acces_token(app_id):
    SCOPES = ["Files.ReadWrite.All"]
    access_token_cache = msal.SerializableTokenCache()
    if os.path.exists("api_token_access.json"):
        access_token_cache.deserialize(open("api_token_access.json", "r").read())

    client = PublicClientApplication(client_id=app_id, token_cache=access_token_cache)
    accounts = client.get_accounts()
    if accounts:
        token_response = client.acquire_token_silent(SCOPES, accounts[0])
        print("found acc")
    else:
        flow = client.initiate_device_flow(scopes=SCOPES)
        print("user code: " + flow["user_code"])
        webbrowser.open(flow["verification_uri"])
        token_response = client.acquire_token_by_device_flow(flow)
        print(token_response)

    with open("api_token_access.json", "w") as _f:
        _f.write(access_token_cache.serialize())
    return token_response


def upload_to_onedrive(file_path, url, timestamp, folder_id):
    load_dotenv()
    accsess_token = generate_acces_token(os.getenv("APP_ID"))
    print(accsess_token)
    headers = {
        "Authorization": "Bearer " + accsess_token["access_token"]
    }

    file_name = os.path.basename(file_path)

    if not os.path.exists(file_path):
        raise Exception(f"{file_name} is not found")

    with open(file_path, "rb")as upload:
        media_content = upload.read()

    request_body = {
        "item": {
            "@microsoft.graph.conflictBehavior": "rename",
            "description": f"URL={url} Timestamp={timestamp}",
            "name": file_name
        }
    }
    response_upload_session = requests.post(
        os.getenv("GRAPH_ENDPOINT") + f"/me/drive/items/{folder_id}:/{file_name}:/createUploadSession",
        headers=headers,
        json=request_body
    )
    print(response_upload_session.json())
    try:
        upload_url = response_upload_session.json()["uploadUrl"]
        response_upload_status = requests.put(upload_url, data=media_content)
        print(f"File: {file_path}")
        print(response_upload_status)
    except Exception as e:
        print(e)

    return get_src_link(file_name, folder_id)

def get_src_link(itemname, folder_id):
    load_dotenv()
    accsess_token = generate_acces_token(os.getenv("APP_ID"))
    print(accsess_token)
    headers = {
        "Authorization": "Bearer " + accsess_token["access_token"]
    }

    items = json.loads(requests.get(os.getenv("GRAPH_ENDPOINT") + f'/me/drive/items/{folder_id}/children', headers=headers).text)
    look_for_item = itemname
    item_id = ''
    items = items['value']
    for entries in range(len(items)):
        if (items[entries]['name'] == look_for_item):
            item_id = items[entries]['id']
            print('Item-id of', look_for_item, ':', item_id)
            break
    if (item_id == ''):
        print(look_for_item, 'not found in the directory.')

    request_body = {
        "type": "embed"
    }
    response_get_emb = requests.post(
        os.getenv("GRAPH_ENDPOINT") + f"/me/drive/items/{item_id}/createLink",
        headers=headers,
        json=request_body
    )
    try:
        return response_get_emb.json()["link"]["webUrl"].replace("embed", "download")
    except:
        return None


def write_url(clipname):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    with open("urls.json", "a") as file:
        file.write("\n" + current_time + " " + clipname)


def delete_all(folder):
    folder_path = os.getcwd()+"\\{}".format(folder)
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if os.path.isfile(file_object_path) or os.path.islink(file_object_path):
            os.unlink(file_object_path)
        else:
            shutil.rmtree(file_object_path)


def main(url):
    load_dotenv()
    cut_video(url)
    write_url(url)
    delete_all("Clips")
    delete_all("Videos")


#if __name__ == "__main__":
    # download_yt_video("https://www.youtube.com/watch?v=y6H8qRLcFCw")
    # time.sleep(20)
    #cut_video("https://www.youtube.com/watch?v=y6H8qRLcFCw")
    #get_startTime_and_endTime("https://www.youtube.com/watch?v=y6H8qRLcFCw")
    # link = "https://www.youtube.com/watch?v=BDbWpN80PT4"
    # download_yt_video(link)
    # print(" ")

#main("https://www.youtube.com/watch?v=xinubELTk8Y")
import shutil
import subprocess
import webbrowser

import msal
from msal import PublicClientApplication
import requests
from dotenv import load_dotenv
import os
import pymongo
from pytube import YouTube
from moviepy.editor import *
import cv2
import moviepy.editor as mp
import re
from moviepy.editor import VideoFileClip
import time
from datetime import datetime
from pytube.cli import on_progress
from scenedetect import open_video, ContentDetector, SceneManager, StatsManager
import pandas as pd
import os.path
import collections

def cut_video(url):
    load_dotenv()
    cluster = pymongo.MongoClient(
        os.getenv("DB_KEY"))
    db = cluster["test"]
    collection = db["comments"]
    # pymongo_cursor = collection.find({})
    all_data = [document for document in collection.find({"$and": [{"Timestamp": {"$ne": None}}, {"URL": "{}".format(url)}]})]
    if all_data == None:
        print("no entrys found in db")
    duration = get_length(os.getcwd()+"\Videos\{}.mp4".format(url[32:43]))

    print("")

    #collection.find({"$and":[{"Timestamp": {"$ne":None}} , {"URL": "{}".format(url)}]})


    # if len(start_time) == 4: # add a 0 if start_time string 0:00 format 00:00 required
    #     to_add = "0"
    #     res = "".join((to_add, string))
    # else:
    #     res = start_time
    #secs = int(res[0:2]) *60 + int(res[3:5])


    #time_format = time.strftime("%M:%S", time.gmtime(secs))
    #end_time = time.strftime("%M:%S", time.gmtime(secs+int(duration)))
    sorted_data = sorted(all_data, key=lambda d: d['Likes'], reverse=True)
    for i in range(len(sorted_data)):
        #try:
        if sorted_data[i]["Starttime"] > round(duration)-1:
            continue

        else:
            clip = VideoFileClip(os.getcwd()+"\Videos\{}.mp4".format(sorted_data[i]["URL"][32:43])).subclip(int(sorted_data[i]["Starttime"]), int(sorted_data[i]["Endtime"]))
            clip.to_videofile(os.getcwd()+"\Clips\clip_{}_{}.mp4".format(sorted_data[i]["URL"][32:43], int(sorted_data[i]["Counter"])), codec="libx264", temp_audiofile='temp-audio.m4a', remove_temp=True, audio_codec='aac')
            clip.close()
            time.sleep(2)
            #clip_duration = all_data[i]["Endtime"] - all_data[i]["Starttime"]
            #add_text_to_video(all_data[i]["Comment"], all_data[i]["URL"][32:43], i, clip_duration)
            add_screen_to_clip(sorted_data[i]["URL"][32:43], int(sorted_data[i]["Counter"]), i, sorted_data[i]["Timestamp"])
            print("final clip done")
        # except:
        #     print("error at URL = "+ sorted_data[i]["URL"][32:43]+ "\n", "Counter= " + str(int(sorted_data[i]["Counter"])))
        #     continue
            #time.sleep(10)

def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)

# def download_yt_video(url):
#     try:
#         if os.path.exists(os.getcwd()+"\Videos" + url[32:43] + ".mp4"):
#             print("Video already exists")
#             pass
#         else:
#             yt = YouTube(url, on_progress_callback=on_progress)
#             stream = yt.streams.get_highest_resolution()
#             print(stream.filesize_approx)
#             stream.download(os.getcwd()+"\Videos", filename=url[32:43] + ".mp4")
#             print('Download Completed!' + stream.title)
#
#             #if os.path.exists(os.getcwd()+"\Videos" + url[32:43] + ".mp4"):
#
#
#
#     except:
#         print("download error")

def add_screen_to_clip(url, counter, i, timestamp):
    video = mp.VideoFileClip(os.getcwd()+"\Clips\clip_{}_{}.mp4".format(url, counter))

    logo = (mp.ImageClip(os.getcwd()+"\screenshots_of_comments\{}\screen_{}.png".format(url, counter))
              .set_opacity(0.8)
              .set_duration(video.duration)
              #.resize(width=video.w-100) # if you need to resize...
              .margin(left=10, bottom=10, opacity=0) # (optional) logo-border padding
              .set_pos(("center", "bottom")))
    final = mp.CompositeVideoClip([video, logo])
    load_dotenv()
    PATH = os.getenv("VIDEO_PATH")
    if not os.path.exists(PATH+r"\Clips_Final\Trends\{}".format(url)):
        os.makedirs(PATH+r"\Clips_Final\Trends\{}".format(url))

    if not os.path.exists(PATH+r"\Clips_Final\Most_Liked_Clips"):
        os.makedirs(PATH+r"\Clips_Final\Most_Liked_Clips")

    # if not os.path.exists(PATH+"\\Clips_Final\\Comedy\\{}".format(url)):
    #     os.makedirs(PATH+"\\Clips_Final\Comedy\\{}".format(url))
    #
    # if not os.path.exists(PATH+"\\Clips_Final\\News\\{}".format(url)):
    #     os.makedirs(PATH+"\\Clips_Final\\News\\{}".format(url))
    #
    # if not os.path.exists(PATH+"\\Clips_Final\\People\\{}".format(url)):
    #     os.makedirs(PATH+"\\Clips_Final\\People\\{}".format(url))

    if i == 0:
        clipname = PATH + rf"\Clips_Final\Most_Liked_Clips\clip_{url}.mp4"
        final.write_videofile(clipname, fps=60, codec="libx264")
        folder_id = os.getenv("FOLDER_ID_MOST_LIKED")
        upload_to_onedrive(clipname, f"https://www.youtube.com/watch?v={url}", timestamp, folder_id)
    else:
        clipname = PATH + rf"\Clips_Final\Trends\clip_{url}_{counter}.mp4"
        final.write_videofile(clipname, fps=60, codec="libx264")
        folder_id = os.getenv("FOLDER_ID_CLIPS")
        upload_to_onedrive(clipname, f"https://www.youtube.com/watch?v={url}", timestamp, folder_id)



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


# def add_text_to_video(comment, url, counter, clip_duration):
#     print("video")
#     comment = re.sub('\d+\d+:+\d+\d', '', comment)
#     comment = re.sub('\d+:+\d+\d', '', comment)
#     if len(comment) < 101:
#         my_video = mp.VideoFileClip(os.getcwd()+"\Clips\clip_{}_{}.mp4".format(url, counter), audio=True)
#         w,h = moviesize = my_video.size
#         my_text = mp.TextClip(comment, font="Amiri-regular", color="white", fontsize=24)
#         txt_col = my_text.on_color(size=(my_video.w, my_text.h+11), color=(0,0,0), pos=(10, "center"), col_opacity=0.6)
#
#
#
#         #txt_mov = txt_col.set_pos( lambda t: (max(w/30,int(w-0.5*w*t)),max(5*h/6,int(100*t))) )
#         final = mp.CompositeVideoClip([my_video,txt_col.set_position((0,my_video.h-my_text.h-50))])
#         final.subclip(0, clip_duration).write_videofile(os.getcwd()+"\Clips_Final\clip_{}_{}.mp4".format(url, counter),fps=60,codec="libx264")
#
#     elif len(comment) <202:
#         comment1 = comment[0:101]
#         comment2 = comment[101:201]
#         comment2 = comment2.lstrip()
#
#         my_video = mp.VideoFileClip(os.getcwd()+"\Clips\clip_{}_{}.mp4".format(url, counter), audio=True)
#         w, h = moviesize = my_video.size
#         my_text = mp.TextClip(comment1, font="Amiri-regular", color="white", fontsize=24)
#         txt_col = my_text.on_color(size=(my_video.w, my_text.h + 11), color=(0, 0, 0), pos=(10, "center"),
#                                    col_opacity=0.6)
#         print(my_text.h)
#         my_text2 = mp.TextClip(comment2, font="Amiri-regular", color="white", fontsize=24)
#         txt_col2 = my_text2.on_color(size=(my_video.w, my_text.h+ 11), color=(0,0,0), pos=(10, "center"), col_opacity=0.6)
#         # ,txt_col2.set_position((0,my_video.h-my_text.h-150))
#
#         # txt_mov = txt_col.set_pos( lambda t: (max(w/30,int(w-0.5*w*t)),max(5*h/6,int(100*t))) )
#         final = mp.CompositeVideoClip([my_video, txt_col.set_position((0, my_video.h - my_text.h - 90)),txt_col2.set_position((0, my_video.h - my_text.h - 50))])
#         final.subclip(0, clip_duration).write_videofile(os.getcwd()+"\Clips_Final\clip_{}_{}.mp4".format(url, counter), fps=30, codec="libx264")

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
    #download_yt_video(url)
    # time.sleep(200)
    # #get_startTime_and_endTime(url)
    # time.sleep(5)
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
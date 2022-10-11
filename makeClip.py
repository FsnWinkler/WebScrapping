import subprocess

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
from scenedetect import open_video, ContentDetector, SceneManager, StatsManager
import pandas as pd
import os.path

def cut_video(url):
    load_dotenv()
    cluster = pymongo.MongoClient(
        os.getenv("db_key"))
    db = cluster["test"]
    collection = db["final_timestamps"]
    # pymongo_cursor = collection.find({})
    all_data = [document for document in collection.find({"URL": "{}".format(url)})]
    if all_data == None:
        print("no entrys found in db")
    duration = get_length(os.getcwd()+"\Videos\{}.mp4".format(all_data[0]["URL"][32:43]))

    print("")


    # if len(start_time) == 4: # add a 0 if start_time string 0:00 format 00:00 required
    #     to_add = "0"
    #     res = "".join((to_add, string))
    # else:
    #     res = start_time
    #secs = int(res[0:2]) *60 + int(res[3:5])


    #time_format = time.strftime("%M:%S", time.gmtime(secs))
    #end_time = time.strftime("%M:%S", time.gmtime(secs+int(duration)))
    try:
        for i in range(len(all_data)):
            if all_data[i]["Starttime"] > round(duration)-1:
                continue
            else:
                clip = VideoFileClip(os.getcwd()+"\Videos\{}.mp4".format(all_data[i]["URL"][32:43])).subclip(all_data[i]["Starttime"], all_data[i]["Endtime"])
                clip.to_videofile(os.getcwd()+"\Clips\clip_{}_{}.mp4".format(all_data[i]["URL"][32:43], i), codec="libx264", temp_audiofile='temp-audio.m4a', remove_temp=True, audio_codec='aac')
                clip.close()
                time.sleep(2)
                clip_duration = all_data[i]["Endtime"] - all_data[i]["Starttime"]
                add_text_to_video(all_data[i]["Comment"], all_data[i]["URL"][32:43], i, clip_duration)
                print("")
    except:
        print("error")
        #time.sleep(10)

def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)

def download_yt_video(url):
    try:
        if os.path.exists(os.getcwd()+"/Videos" + url[32:43] + ".mp4"):
            pass
        else:
            yt = YouTube(url)
            stream = yt.streams.get_highest_resolution()
            print(stream.filesize_approx)
            stream.download(os.getcwd()+"/Videos", filename=url[32:43] + ".mp4")
            print('Task Completed!')
            return(stream.title)

    except:
        print("error")


def add_text_to_video(comment, url, counter, clip_duration):
    print("video")
    comment = re.sub('\d+\d+:+\d+\d', '', comment)
    comment = re.sub('\d+:+\d+\d', '', comment)
    if len(comment) < 101:
        my_video = mp.VideoFileClip(os.getcwd()+"\Clips\clip_{}_{}.mp4".format(url, counter), audio=True)
        w,h = moviesize = my_video.size
        my_text = mp.TextClip(comment, font="Amiri-regular", color="white", fontsize=24)
        txt_col = my_text.on_color(size=(my_video.w, my_text.h+11), color=(0,0,0), pos=(10, "center"), col_opacity=0.6)



        #txt_mov = txt_col.set_pos( lambda t: (max(w/30,int(w-0.5*w*t)),max(5*h/6,int(100*t))) )
        final = mp.CompositeVideoClip([my_video,txt_col.set_position((0,my_video.h-my_text.h-50))])
        final.subclip(0, clip_duration).write_videofile(os.getcwd()+"\Clips_Final\clip_{}_{}.mp4".format(url, counter),fps=60,codec="libx264")

    elif len(comment) <202:
        comment1 = comment[0:101]
        comment2 = comment[101:201]
        comment2 = comment2.lstrip()

        my_video = mp.VideoFileClip(os.getcwd()+"\Clips\clip_{}_{}.mp4".format(url, counter), audio=True)
        w, h = moviesize = my_video.size
        my_text = mp.TextClip(comment1, font="Amiri-regular", color="white", fontsize=24)
        txt_col = my_text.on_color(size=(my_video.w, my_text.h + 11), color=(0, 0, 0), pos=(10, "center"),
                                   col_opacity=0.6)
        print(my_text.h)
        my_text2 = mp.TextClip(comment2, font="Amiri-regular", color="white", fontsize=24)
        txt_col2 = my_text2.on_color(size=(my_video.w, my_text.h+ 11), color=(0,0,0), pos=(10, "center"), col_opacity=0.6)
        # ,txt_col2.set_position((0,my_video.h-my_text.h-150))

        # txt_mov = txt_col.set_pos( lambda t: (max(w/30,int(w-0.5*w*t)),max(5*h/6,int(100*t))) )
        final = mp.CompositeVideoClip([my_video, txt_col.set_position((0, my_video.h - my_text.h - 90)),txt_col2.set_position((0, my_video.h - my_text.h - 50))])
        final.subclip(0, clip_duration).write_videofile(os.getcwd()+"\Clips_Final\clip_{}_{}.mp4".format(url, counter), fps=30, codec="libx264")

def get_startTime_and_endTime(url):
    load_dotenv()
    cluster = pymongo.MongoClient(
        os.getenv("db_key"))
    db = cluster["test"]
    collection = db["timestamps"]
    #pymongo_cursor = collection.find({})
    all_data = [document for document in collection.find({"URL" : "{}".format(url)})]
    if all_data == None:
        print("no entrys found in db")
    #all_data = list(pymongo_cursor)


    comment_arr = []
    author_arr = []
    URL_arr = []
    timestamp_arr = []

    for i in range(len(all_data)):
        comment = all_data[i]["Comment"]
        comment = re.sub('\d+\d+:+\d+\d', '', comment)
        comment = re.sub('\d+:+\d+\d', '', comment)
        comment_arr.append(comment)
        author_arr.append(all_data[i]["Author"])
        URL_arr.append(all_data[i]["URL"])

        if len(all_data[i]["Timestamp"]) == 4:  # add a 0 if start_time string 0:00 format 00:00 required
            to_add = "0"
            res = "".join((to_add, all_data[i]["Timestamp"]))
        else:
            res = all_data[i]["Timestamp"]

        timestamp_arr.append(res)



    comment_author_url_timestamp_df = pd.DataFrame({"Comment": comment_arr, "Author": author_arr, "URL": URL_arr, "Timestamp": timestamp_arr})
    #filtered_df = comment_author_url_timestamp_df.loc[comment_author_url_timestamp_df["URL"] == url]
    times_df = comment_author_url_timestamp_df["Timestamp"].dropna(0)#.where(comment_author_url_timestamp_df["URL"] == "https://www.youtube.com/watch?v=QPJH4d8s1yM")

    timestamps = []
    try:
        for i in range(len(times_df)):
            timestamp = times_df.loc[i]
            as_secounds = int(timestamp[0:2]) * 60 + int(timestamp[3:5])
            timestamps.append(as_secounds)
    except:
        print("error")



    begin_of_scenes = find_scenes(os.getcwd()+"\Videos\{}.mp4".format(url[32:43]))
    start_and_endtime = {"Starttime": [], "Endtime": []}

    # for i in range(len(timestamps)):
    #     for y in range(len(begin_of_scenes)):
    #         if timestamps[i] <= begin_of_scenes[y]+10 and timestamps[i] <= begin_of_scenes[y]+15:
    #             if timestamps[i]-begin_of_scenes[y] <= 10:
    #                 start_and_endtime["Starttime"].append(timestamps[i])
    #                 start_and_endtime["Endtime"].append(begin_of_scenes[y])
    #             start_and_endtime["Starttime"].append(timestamps[i])
    #             start_and_endtime["Endtime"].append(begin_of_scenes[y])
    #             break
    #         elif y ==len(begin_of_scenes):
    #             start_and_endtime["Starttime"].append(timestamps[i])
    #             start_and_endtime["Endtime"].append(timestamps[i]+15)
    try:
        for i in range(len(timestamps)):
            for y in range(len(begin_of_scenes)):
                if timestamps[i] < begin_of_scenes[y]:
                    if (begin_of_scenes[y] - timestamps[i]) > 8 and (begin_of_scenes[y] - timestamps[i]) < 30:
                        start_and_endtime["Starttime"].append(timestamps[i])
                        start_and_endtime["Endtime"].append(begin_of_scenes[y])
                        break
                if y + 1 == len(begin_of_scenes):
                    start_and_endtime["Starttime"].append(timestamps[i])
                    start_and_endtime["Endtime"].append(timestamps[i] + 15)
    except:
        print("error")

    liste = []
    try:
        for i in range(len(timestamps)):
            liste.append(start_and_endtime["Endtime"][i] - start_and_endtime["Starttime"][i])
    except:
        print("timestamp error")
    print(liste)
    final_df = pd.DataFrame({"Comment": comment_arr, "Author": author_arr, "URL": URL_arr, "Starttime": start_and_endtime["Starttime"], "Endtime": start_and_endtime["Endtime"]})

    print("")


    load_dotenv()
    cluster = pymongo.MongoClient(os.getenv("db_key"))
    db = cluster["test"]


    collection = db["final_timestamps"]
    for i in range(len(final_df)):
        if collection.find_one({"Comment": final_df["Comment"].iloc[i]}):
            continue
            #dataset = collection.find_one({"Comment": final_df["Comment"].iloc[i]})
            # if dataset.get("Likes") < final_df["Likes"].iloc[i]:
            #     newvalues = {"$set": {"Likes": final_df["Likes"].iloc[i]}}
            #     collection.update_one(dataset, newvalues)
            #     print("succsessfully  updated {} to {}  into database".format(dataset, newvalues))
            # else:
            #     print("Likes are up to date!")

        else:
            # record_to_insert = data.loc[i].to_dict("list")
            collection.insert_one(final_df.iloc[i].to_dict())
            print("succsessfully inserted {}  into database".format(final_df.iloc[i]))



def find_scenes(video_path):
    # type: (str) -> List[Tuple[FrameTimecode, FrameTimecode]]

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

def main(url):
    download_yt_video(url)
    time.sleep(20)
    get_startTime_and_endTime(url)
    time.sleep(5)
    cut_video(url)


if __name__ == "__main__":
    # download_yt_video("https://www.youtube.com/watch?v=y6H8qRLcFCw")
    # time.sleep(20)
    #cut_video("https://www.youtube.com/watch?v=y6H8qRLcFCw")
    #get_startTime_and_endTime("https://www.youtube.com/watch?v=y6H8qRLcFCw")
    # link = "https://www.youtube.com/watch?v=BDbWpN80PT4"
    # download_yt_video(link)
    # print(" ")
    main("https://www.youtube.com/watch?v=BDbWpN80PT4")
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


def cut_video(video_title, start_time, duration):
    # if len(start_time) == 4: # add a 0 if start_time string 0:00 format 00:00 required
    #     to_add = "0"
    #     res = "".join((to_add, string))
    # else:
    #     res = start_time
    secs = int(res[0:2]) *60 + int(res[3:5])


    #time_format = time.strftime("%M:%S", time.gmtime(secs))
    end_time = time.strftime("%M:%S", time.gmtime(secs+int(duration)))


    clip = VideoFileClip(os.getcwd()+"\Videos\{}.mp4".format(video_title)).subclip(res, end_time)
    clip.to_videofile(os.getcwd()+"\Clips\clip_{}.mp4".format(video_title), codec="libx264", temp_audiofile='temp-audio.m4a', remove_temp=True, audio_codec='aac')
    clip.close()


def download_yt_video(link):
    try:
        yt = YouTube(link)
        stream = yt.streams.get_highest_resolution()
        print(stream.filesize_approx)
        stream.download(os.getcwd()+"/Videos")
        print('Task Completed!')
        return(stream.title)

    except:
        print("error")


def search_db_for_videos():
    load_dotenv()
    cluster = pymongo.MongoClient(os.getenv("db_key"))
    db = cluster["test"]
    collection = db["timestamp"]
    for x in collection.find({}, {"Timestamp":1, "_id":0}):
      print(x["Timestamp"])

    link =""

    for x in collection.find({}, {"URL":1, "_id":0}):
        link = x["URL"]

    comment = ""
    for x in collection.find({}, {"Comment":1, "_id":0}):
        comment = x["Comment"]



def add_text_to_video(comment):
    comment = re.sub('\d+\d+:+\d+\d', '', comment)
    comment = re.sub('\d+:+\d+\d', '', comment)
    if len(comment) < 101:
        my_video = mp.VideoFileClip("clip.mp4", audio=True)
        w,h = moviesize = my_video.size
        my_text = mp.TextClip("Author: "+ comment, font="Amiri-regular", color="white", fontsize=24)
        txt_col = my_text.on_color(size=(my_video.w, my_text.h+11), color=(0,0,0), pos=(10, "center"), col_opacity=0.6)


        #txt_mov = txt_col.set_pos( lambda t: (max(w/30,int(w-0.5*w*t)),max(5*h/6,int(100*t))) )
        final = mp.CompositeVideoClip([my_video,txt_col.set_position((0,my_video.h-my_text.h-50))])
        final.subclip(0,20).write_videofile("test.mp4",fps=60,codec="libx264")

    elif len(comment) <202:
        comment1 = comment[0:101]
        comment2 = comment[101:201]
        comment2 = comment2.lstrip()

        my_video = mp.VideoFileClip("clip.mp4", audio=True)
        w, h = moviesize = my_video.size
        my_text = mp.TextClip("Author: " + comment1, font="Amiri-regular", color="white", fontsize=24)
        txt_col = my_text.on_color(size=(my_video.w, my_text.h + 11), color=(0, 0, 0), pos=(10, "center"),
                                   col_opacity=0.6)
        print(my_text.h)
        my_text2 = mp.TextClip(comment2, font="Amiri-regular", color="white", fontsize=24)
        txt_col2 = my_text2.on_color(size=(my_video.w, my_text.h+ 11), color=(0,0,0), pos=(10, "center"), col_opacity=0.6)
        # ,txt_col2.set_position((0,my_video.h-my_text.h-150))

        # txt_mov = txt_col.set_pos( lambda t: (max(w/30,int(w-0.5*w*t)),max(5*h/6,int(100*t))) )
        final = mp.CompositeVideoClip([my_video, txt_col.set_position((0, my_video.h - my_text.h - 90)),txt_col2.set_position((0, my_video.h - my_text.h - 50))])
        final.subclip(0, 20).write_videofile("test.mp4", fps=30, codec="libx264")

def get_startTime_and_endTime(url):
    cluster = pymongo.MongoClient(
        os.getenv("db_key"))
    db = cluster["test"]
    collection = db["timestamps"]
    pymongo_cursor = collection.find()
    all_data = list(pymongo_cursor)


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
    filtered_df = comment_author_url_timestamp_df.loc[comment_author_url_timestamp_df["URL"] == url]

    timestamps = []

    for i in range(len(comment_author_url_timestamp_df)):
        timestamp = comment_author_url_timestamp_df.loc[i]["Timestamp"]
        as_secounds = int(timestamp[0:2]) * 60 + int(timestamp[3:5])
        timestamps.append(as_secounds)



    begin_of_scenes = find_scenes("video1.mp4")
    start_and_endtime = {"Starttime":[], "Endtime":[]}

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
    for i in range(len(timestamps)):
        for y in range(len(begin_of_scenes)):
            if timestamps[i] < begin_of_scenes[y]:
                if (begin_of_scenes[y] - timestamps[i]) > 5 and (begin_of_scenes[y] - timestamps[i]) < 40:
                    start_and_endtime["Starttime"].append(timestamps[i])
                    start_and_endtime["Endtime"].append(begin_of_scenes[y])
                    break
            if y + 1 == len(begin_of_scenes):
                start_and_endtime["Starttime"].append(timestamps[i])
                start_and_endtime["Endtime"].append(timestamps[i] + 15)

    list = []
    for i in range(len(timestamps)):
        list.append(start_and_endtime["Endtime"][i] - start_and_endtime["Starttime"][i])

    print("")


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

def main():
    pass

if __name__ == "__main__":
    #download_yt_video("https://www.youtube.com/watch?v=BDbWpN80PT4")
    string = "0:10"



    cut_video("vid1", "01:10", "20")
    main()
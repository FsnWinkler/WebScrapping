from dotenv import load_dotenv
import os
import pymongo
from pytube import YouTube
from moviepy.editor import *
import cv2
import moviepy.editor as mp
import re
from moviepy.editor import VideoFileClip


def cut_video(video_path, start_time, end_time, clip_name):
    clip = VideoFileClip("50€ SPRINT DUELL! - feat Mois.mp4").subclip("01:10", "01:30")
    clip.to_videofile("clip.mp4", codec="libx264", temp_audiofile='temp-audio.m4a', remove_temp=True, audio_codec='aac')


def download_yt_video(link):
    try:
        yt = YouTube(link)
        stream = yt.streams.get_highest_resolution()
        print(stream.filesize_approx)
        stream.download(os.getcwd()+"/Videos")

        print('Task Completed!')
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

def main():
    pass

if __name__ == "__main__":
    download_yt_video("https://www.youtube.com/watch?v=EJPl0EHAZiY")
    main()
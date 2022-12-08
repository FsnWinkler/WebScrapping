from numify import numify


class Comment:
    def __init__(self, comment, url, author, timestamp, likes, counter, begin_of_scenes, title):
        self.comment = comment
        self.url = url
        self.author = format_author(author)
        self.timestamp = format_timestamp(timestamp)
        self.likes = format_likes(likes)
        self.counter = counter
        self.starttime = timestamp_string_to_secounds(format_timestamp(timestamp))
        self.endtime = find_endtime(timestamp_string_to_secounds(format_timestamp(timestamp)), begin_of_scenes)
        self.title = title
        self.comment_dict = {
            "Comment": self.comment,
             "URL": self.url,
             "Author": self.author,
             "Timestamp": self.timestamp,
             "Likes": self.likes,
             "Counter": self.counter,
             "Starttime": self.starttime,
             "Endtime": self.endtime,
             "Title" : self.title
        }


def find_endtime(starttime, begin_of_scenes):
    for y in range(len(begin_of_scenes)):
        if starttime < begin_of_scenes[y]:
            if (begin_of_scenes[y] - starttime) > 8 and (begin_of_scenes[y] - starttime) < 30:
                end_time = begin_of_scenes[y]
                return end_time

        if y + 1 == len(begin_of_scenes):
            end_time = starttime + 15
            return end_time

def format_author(author):
    new_item = author.replace("\n", "")
    final_item = new_item.replace(" ", "")
    return final_item
def timestamp_string_to_secounds(timestamp):
    if len(timestamp) == 5:
         return int(int(timestamp[0:2]) * 60 + int(timestamp[3:5]))
    elif len(timestamp) == 8:
        return int(int(timestamp[0:2]) * 60 + int(timestamp[3:5]) + int(timestamp[6:8]))

def format_likes(like):
    replace_breaks = like.replace("\n", "")
    replace_coma = replace_breaks.replace(",", ".")
    replace_blanks = replace_coma.replace(" ", "")

    if "K" in replace_blanks or "k" in replace_blanks:
        final_like = numify.numify(replace_blanks)
        return final_like
    else:
        return replace_blanks
def format_timestamp(timestamp):
    to_add_at_start = "0"
    if len(timestamp) == 5 or len(timestamp) == 8:
        return timestamp
    elif len(timestamp) == 4:
        return "".join((to_add_at_start, timestamp))
    elif len(timestamp) == 7:
        return "".join((to_add_at_start, timestamp[0]))

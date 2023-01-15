import datetime
from os import path
from random import random
import datetime
import urllib.parse

from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_rangerequest import RangeRequest

from feedgen.feed import FeedGenerator

from downloader import *

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
# app.config["PREFERRED_URL_SCHEME"] = "https"


def serve_file(file_path):
    size = path.getsize(file_path)
    last_modified = datetime.datetime.utcnow()
    with open(file_path, "rb") as f:
        etag = RangeRequest.make_etag(f)
    res = RangeRequest(
        open(file_path, "rb"),
        etag=etag,
        size=size,
        last_modified=last_modified,
    ).make_response()

    res.headers["Content-Type"] = "audio/mp4"  # Chromium really cares about this
    res.headers["Content-Disposition"] = "inline"

    return res


@app.route("/")
def index():
    return """
        <h1>Paul's Little Podcast Maker</h1>
        <p>Paste a link to a YouTube channel's videos page or Playlist to turn it into an audio RSS feed that you can add to your podcast client. </p>
        <p>Check whether the feed is interpreted correctly by clicking "Preview Feed"; on that page you can get the link to your RSS feed. </p>
        <form action="playlist_info">
            <label for="url">Channel or Playlist URL</label>
            <input name="url" type="url" />
            <input type="submit" value="Preview Feed" />
        </form>

        <p>You can also get the audio of a single video by clicking the links or by inserting the URL here:</p>
        <form action="stream">
            <label for="url">Video URL</label>
            <input name="url" type="url" />
            <input type="submit" value="Stream Audio" />
        </form>
    """


@app.route("/playlist_info")
def playlist_info():
    url = request.args["url"]
    playlist = get_playlist_info(url)

    page = f"<h1>{playlist['title']}</h1>"
    feed_url = f"{request.host_url}feed?url={urllib.parse.quote(url)}"
    page += f'<a href="{feed_url}">RSS Feed</a>'
    page += "<ul>"
    for video in playlist["videos"]:
        stream_url = "stream?url=" + urllib.parse.quote(video["url"])
        page += f"<li><a href={stream_url}>{video['title']}</a></li>"
    page += "</ul>"
    return page


@app.route("/feed")
def feed():
    url = request.args["url"]
    playlist = get_playlist_info(url)

    fg = FeedGenerator()
    fg.load_extension("podcast")  # this includes the content of podcast_entry

    fg.podcast.itunes_category("Podcasting")

    fg.title(playlist["title"] or playlist["id"])
    fg.description(
        f"{playlist['description'] or ''}</br></br> created from <a href={playlist['url']}>{playlist['url']}"
    )
    fg.link(href=request.url, rel="self")

    videos = playlist["videos"]

    # To get our fake date, we iterate from the end and increase the date each time
    # This has the effect that new episodes get newer dates while old ones keep theirs
    fake_date_start = datetime.datetime.combine(
        datetime.datetime.fromisocalendar(1980, 1, 1),
        datetime.time(0, 0, 0),
        datetime.timezone.utc,
    )

    i = 0
    for video in reversed(videos):
        fe = fg.add_entry(order="prepend")

        fe.comments(f"Index: {i}")

        stream_url = request.host_url + "stream?url=" + urllib.parse.quote(video["url"])
        id = video["id"]
        title = video["title"]
        description = f"{video['description'] or ''}</br> Created from <a href={video['url']}>{video['url']}</a>"
        length = int(video["duration"] or 0)  # in seconds

        # Todo: Get actual release date. This will allow the podcatcher to better sort the videos and tell when there is "new" content
        date = fake_date_start + datetime.timedelta(days=i)

        fe.id(id)
        fe.title(title)
        fe.description(description)
        fe.enclosure(url=stream_url, type="audio/mp4", length=str(length).encode())
        fe.podcast.itunes_duration(length)
        fe.pubDate(date)
        fe.podcast.itunes_order(i)  # Apparently no effect
        # Todo: Add itunes episode number. This will be hard because it's not supported by feedgen.
        # fe.podcast.itunes_episode(i)
        i += 1

    return fg.rss_str(pretty=True)


@app.route("/stream")
def stream():
    url = request.args["url"]
    fp = get_file(url)
    return serve_file(fp)


if __name__ == "__main__":
    app.run(port=8000, debug=True, host="0.0.0.0")

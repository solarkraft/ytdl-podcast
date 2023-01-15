import os
import json

import yt_dlp


def get_playlist_info(url):
    opts = {
        "simulate": True,  # Avoid accidentally downloading full videos
        "extract_flat": True,  # Do not download specific video info, we just want the index ("in_playlist" is equivalent for this use case)
        # Todo: Get real dates
        # "extractor_args": {"youtubetab": {
        #     "approximate_date": "a" # can be any string for true
        # }},
    }

    with yt_dlp.YoutubeDL(opts) as dl:
        playlist_info_verbose = dl.extract_info(url)

        print("Playlist info (verbose):", json.dumps(playlist_info_verbose, indent=4))

        playlist_info_simplified = {
            "id": playlist_info_verbose["id"],
            "url": playlist_info_verbose["webpage_url"],
            "title": playlist_info_verbose.get("title"),
            "author": playlist_info_verbose.get("uploader"),
            "description": playlist_info_verbose.get("description"),
            "videos": list(
                map(
                    lambda v: {
                        "id": v.get("id"),
                        "url": v["url"],
                        "title": v["title"],
                        "duration": v.get("duration"),
                        "description": v.get("description"),
                    },
                    playlist_info_verbose["entries"],
                )
            ),
        }
    return playlist_info_simplified


def get_file(url):
    print("Got request for", url)

    # Caching is quite important because some clients like firing repeated range requests
    cache_dir = "/tmp/youtube_dl/"
    os.makedirs(cache_dir, exist_ok=True)

    file_name = url.replace("/", "_")
    file_path = cache_dir + file_name

    if os.path.isfile(file_path):
        print("Nice, it's already cached")
        return file_path

    print("It's not cached, let's download ...")

    opts = {
        # "quiet": True,
        "format": "139",  # mid ("low") quality m4a (but the quality is actually quite good)
        # Todo: Allow more formats. Format 139 is very common, but there are rare cases on YouTube in which it's not available.
        # It's also never available on other sites.
        "outtmpl": {"default": file_path},
    }

    with yt_dlp.YoutubeDL(opts) as dl:
        dl.download([url])

    return file_path

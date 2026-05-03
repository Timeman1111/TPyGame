import tpygame as tpy
import requests
import cv2
import time
import pathlib
import sys



TEST_VIDEO_PATH = "scripts/test_files/random_video.mp4"

def ensure_test_video():
    if not pathlib.Path(TEST_VIDEO_PATH).exists():
        print("Downloading test video...")
        pathlib.Path("scripts/test_files").mkdir(parents=True, exist_ok=True)
        video_req = requests.get('https://lorem.video/360p')
        if video_req.status_code != 200:
            raise Exception("Failed to download video")
        with open(TEST_VIDEO_PATH, 'wb') as f:
            f.write(video_req.content)

def main():
    ensure_test_video()


    proc_count = 2
    thread_count = 2

    cfg = tpy.render.parallel.ParallelConfig(enabled=True, num_processes=proc_count, num_threads=thread_count)

    ts = tpy.render.screen.Screen()
    ts.hide_cursor()

    # Use auto_resize=True to follow terminal size
    vid = tpy.render.video.Video(
        source=TEST_VIDEO_PATH,
        auto_resize=True,
    )

    print("Playing video with auto_resize=True. Resize your terminal to test!")
    time.sleep(1)

    try:
        while vid.next_frame():
            vid.draw(ts)
            vid.refresh(ts)
            # No sleep or small sleep for smooth playback
    except KeyboardInterrupt:
        pass
    finally:
        ts.show_cursor()
        tpy.render.term_utils.clear()

if __name__ == "__main__":
    main()

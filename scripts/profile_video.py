
import cProfile
import pstats
import pathlib
import cv2
import requests
import tpygame as tpy

TEST_VIDEO_PATH = "scripts/test_files/random_video.mp4"

def test_video():

    if pathlib.Path(TEST_VIDEO_PATH).exists():
        vid_cap = cv2.VideoCapture(TEST_VIDEO_PATH)
        return vid_cap
    else:
        video_req = requests.get('https://lorem.video/360p')
        if video_req.status_code != 200:
            raise Exception("Failed to download video")
        with open(TEST_VIDEO_PATH, 'wb') as f:
            f.write(video_req.content)
        test_video()

    return


def main():

    screen = tpy.render.screen.Screen()
    video = tpy.render.video.Video(source=TEST_VIDEO_PATH, auto_resize=True)


    while video.next_frame():
        video.draw(screen)
        video.refresh(screen)



if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    main()
    profiler.disable()

    print("\n\n\n")


    stats = pstats.Stats(profiler)
    # Replace 'my_project_folder' with your actual directory name or script name
    stats.sort_stats('cumtime')
    stats.print_stats(10)




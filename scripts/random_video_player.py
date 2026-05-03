import tpygame as tpy
import requests
import cv2
import time
import pathlib

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
    ts = tpy.render.screen.Screen()

    out_size = 0.5
    video_position = (0, 0)

    # Ensure test video exists
    test_video()

    # Get video properties for scaling
    vid_cap = cv2.VideoCapture(TEST_VIDEO_PATH)
    width = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH) * out_size)
    height = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * out_size)
    vid_cap.release()

    # Use the new Video class features
    vid = tpy.render.video.Video(
        x=video_position[0],
        y=video_position[1],
        width=width,
        height=height,
        source=TEST_VIDEO_PATH,
        bitrate=99999999
    )

    while vid.next_frame():


        vid.draw(ts)
        vid.refresh(ts)






if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        tpy.render.term_utils.clear()
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
        video_req = requests.get('https://lorem.video/240p')
        if video_req.status_code != 200:
            raise Exception("Failed to download video")
        with open(TEST_VIDEO_PATH, 'wb') as f:
            f.write(video_req.content)
        test_video()

    return






def main():
    ts = tpy.render.Screen()
    size = 240

    out_size = 0.25
    video_position = (0, 0)


    vid_cap = test_video()

    fps = vid_cap.get(cv2.CAP_PROP_FPS)


    fps_wait_time = 1 / fps

    width = vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # float
    height = vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float

    vid = tpy.video.Video(x=video_position[0], y=video_position[1], width=int(width), height=int(height))
    count = 0


    while vid_cap.isOpened():
        count += 1
        ret, frame = vid_cap.read()

        if not ret:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = cv2.resize(frame, (round(width * out_size), round(height * out_size)))

        vid.input(frame)


        vid.draw(ts)
        ts.refresh()
        ts.move_to_bottom()





if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        tpy.term_utils.clear()
import tpygame as tpy
import requests
import cv2
import time

def main():
    ts = tpy.render.Screen()
    size = 240

    out_size = 0.5
    video_position = (0, 0)


    vid_cap = cv2.VideoCapture(f'https://lorem.video/{size}p')

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
        ts.refresh(force_full=True)

        wait = max(float(0), fps_wait_time)
        time.sleep(wait)




if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        tpy.term_utils.clear()
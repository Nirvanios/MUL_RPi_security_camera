import argparse
import time

import cv2
import imutils

import Camera
import Tracking
import VideoUtils

writer = None


def init_arg_parse():
    parser = argparse.ArgumentParser(description="MUL project")
    parser.add_argument("--video", required=True, dest='video_path', type=str)
    parser.add_argument("--area", required=True, dest='min_area', type=int)
    parser.add_argument("--tracker", default='kcf', dest='tracker', type=str)
    return parser


def main(camera, args):
    detector = Tracking.ChangeDetector(camera.capture_image(), (args.min_area, args.min_area * 3), 500)
    det = Tracking.PersonDetector()
    searching = True
    tracker = None
    hog_fail_cnt = 0
    while True:
        frame = camera.capture_image()

        if frame is None:
            return None
        frame = imutils.resize(frame, width=500)

        if searching:
            found, bb = detector.detect(frame)
            if found:
                rects, _ = det.detect(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), bb)
                if len(rects) != 0:
                    bb = rects[0]
                    print("hog found in searching")
                print("found")
                searching = False
                tracker = Tracking.PersonTracker(args.tracker, frame, bb, 500)
                continue
            else:
                print("not found")

        if not searching:
            success, box = tracker.update(frame)
            if success:
                print("success")
                (x, y, w, h) = [int(v) for v in box]
                rects, weights = det.detect(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (x - 20, y - 20, w + 40, h + 40))
                if len(rects) != 0:
                    (x, y, w, h) = rects[0]
                    tracker = Tracking.PersonTracker(args.tracker, frame, (x, y, w, h), 500)
                    print("hog found in searching")
                    hog_fail_cnt = 0
                else:
                    hog_fail_cnt += 1
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                searching = True
                print("not success")

            if hog_fail_cnt == 50:
                print("set searching true")
                hog_fail_cnt = 0
                searching = True
            writer.write_frame(frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break


if __name__ == "__main__":
    parser = init_arg_parse()
    args = parser.parse_args()
    # camera = VideoUtils.CameraMock(args.video_path)
    # camera.open()
    writer = VideoUtils.VideoWriter("/home/pi/Desktop/out/test.mp4", (640, 480), 10.0)

    det = Tracking.PersonDetector()

    # img = camera.capture_image()
    try:
        # main(camera, args)
        cam = Camera.Camera()
        while True:
            start_time = time.time()
            frame = cam.capture_image()
            # frame = imutils.resize(frame, width=500)
            writer.write_frame(frame)
            print("FPS: ", 1.0 / (time.time() - start_time))
    finally:
        writer.close()

import argparse

import cv2
from imutils.video import FPS

import Tracking


def init_arg_parse():
    parser = argparse.ArgumentParser(description="MUL project")
    parser.add_argument("--video", required=True, dest='video_path', type=str)
    return parser


def main():
    print("CV version: " + str(cv2.__version__))
    parser = init_arg_parse()
    args = parser.parse_args()

    camera = Tracking.CameraMock(args.video_path)
    camera.open()
    initBB = None
    fps = FPS().start()
    try:
        width, height = camera.get_resolution()
        writer = Tracking.VideoWriter('/Users/petr/Desktop/out.mp4', (width, height), 30)
        tracker = Tracking.Tracker()
        try:
            img = camera.capture_image()
            cnt = 0
            while img is not None:
                cnt += 1
                img = camera.capture_image()

                if initBB is not None:
                    (success, box) = tracker.tr.update(img)

                    if success:
                        (x, y, w, h) = [int(v) for v in box]
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    fps.update()
                    fps.stop()

                    print("Frame: " + str(cnt) + ", FPS: " + str(fps.fps()))

                cv2.imshow("Frame", img)
                key = cv2.waitKey(1) & 0xFF

                if key == ord("s"):
                    initBB = cv2.selectROI("Frame", img, fromCenter=False,
                                           showCrosshair=True)

                    tracker.tr.init(img, initBB)
                    fps = FPS().start()

                writer.write_frame(img)
        finally:
            writer.close()
    finally:
        camera.close()


if __name__ == "__main__":
    main()

import argparse

import cv2
import imutils
from imutils.video import FPS

import Tracking
import VideoUtils


def init_arg_parse():
    parser = argparse.ArgumentParser(description="MUL project")
    parser.add_argument("--video", required=True, dest='video_path', type=str)
    parser.add_argument("--area", required=True, dest='min_area', type=int)
    parser.add_argument("--tracker", default='kcf', dest='tracker', type=str)
    return parser


def main1(box, camera):
    initBB = box
    fps = FPS().start()
    tracker = Tracking.Tracker()
    img = camera.capture_image()
    if img is None:
        return
    img = imutils.resize(img, width=500)
    cnt = 0
    tracker.tr.init(img, initBB)
    while img is not None:
        cnt += 1
        img = camera.capture_image()
        img = imutils.resize(img, width=500)
        if img is None:
            return

        if initBB is not None:
            (success, box) = tracker.tr.update(img)

            if success:
                (x, y, w, h) = [int(v) for v in box]
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                return

            fps.update()
            fps.stop()

            print("Frame: " + str(cnt) + ", FPS: " + str(fps.fps()))

        cv2.imshow("Camera", img)
        key = cv2.waitKey(1) & 0xFF


def main(camera, args):
    detector = Tracking.ChangeDetector(camera.capture_image(), (args.min_area, args.min_area * 3), 500)
    searching = True
    tracker = None
    while True:
        frame = camera.capture_image()

        if frame is None:
            return None
        frame = imutils.resize(frame, width=500)

        if searching:
            found, bb = detector.detect(frame)
            if found:
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
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                searching = True
                print("not success")

        """if avg is None:
            avg = gray.copy().astype("float")
            continue

        cv2.accumulateWeighted(gray, avg, 0.3)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

        thresh = cv2.threshold(frameDelta, 5, 255,
                               cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        last_area = 0
        bb = None
        for c in cnts:
            area = cv2.contourArea(c)
            (x, y, w, h) = cv2.boundingRect(c)
            if area > args.min_area and x > 10 and x < 130 and area > last_area:
                bb = (x, y, w, h)
                last_area = area
            else:
                continue

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        if bb is not None:
            return bb"""

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1) & 0xFF


if __name__ == "__main__":
    parser = init_arg_parse()
    args = parser.parse_args()
    camera = VideoUtils.CameraMock(args.video_path)
    camera.open()
    cv2.waitKey()
    main(camera, args)

    """while camera.is_running():
        a = main(camera, args)
        if a is None:
            break
        main1(a, camera)"""

import argparse
import datetime
import time

import cv2
import imutils

import Camera
import Tracking
import VideoUtils
from GeometryUtils import BoundingBox

writer = None


def init_arg_parse():
    parser = argparse.ArgumentParser(description="MUL project")
    parser.add_argument("--video", required=True, dest='video_path', type=str)
    parser.add_argument("--area", required=True, dest='min_area', type=int)
    parser.add_argument("--tracker", default='kcf', dest='tracker', type=str)
    parser.add_argument("--enable_imshow", dest='imshow', default=False, action='store_true')
    parser.add_argument("--print_fps", dest='fps', default=False, action='store_true')
    parser.add_argument("--bb_dist", dest='bb_dist', default=0, type=float)
    return parser


def __unused__old_main(camera, args):
    detector = Tracking.ChangeDetector(camera.capture_image(), (args.min_area, args.min_area * 3), 480)
    det = Tracking.PersonDetector()
    searching = True
    tracker = None
    hog_fail_cnt = 0
    while True:
        start_time = time.time()
        frame = camera.capture_image()

        if frame is None:
            return None
        frame = imutils.resize(frame, width=480)

        if searching:
            found, bb = detector.detect(frame)
            if found:
                rects, _ = det.detect(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), bb)
                if len(rects) != 0:
                    bb = rects[0]
                    print("hog found in searching")
                print("found")
                # searching = False
                tracker = Tracking.PersonTracker(args.tracker, frame, bb, 480)
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
                    tracker = Tracking.PersonTracker(args.tracker, frame, (x, y, w, h), 480)
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
            # writer.write_frame(frame)
        if args.imshow:
            cv2.imshow("a", frame)
        key = cv2.waitKey(1) & 0xFF
        print("FPS:", 1.0 / (time.time() - start_time))
        if key == ord('q'):
            break



def alt_main(camera, args):
    img = camera.capture_image()
    detector = Tracking.ChangeLocator(img, 5)
    tracked = None
    while img is not None:
        start_time = time.time()
        bbs = detector.detect_change(img)
        if len(bbs) > 0:
            if tracked is None:
                tracked = Tracking.TrackedObject(datetime.datetime.now())
            else:
                tracked.reset_lost()
            boxes = []
            for bb in bbs:
                boxes.append(BoundingBox.create_cv(bb))

            change = True
            while change:
                change = False
                for box in boxes:
                    for box2 in boxes:
                        if box == box2:
                            continue
                        if box.distance(box2) < args.bb_dist:
                            boxes[boxes.index(box)] = box.combine(box2)
                            boxes.remove(box2)
                            change = True
                            break
            fin = None
            for box in boxes:
                if box.area() > args.min_area and 1.5 * box.width() < box.height():
                    if fin is None:
                        fin = box
                        continue
                    if box.area() > fin.area():
                        fin = box

            if fin is not None:
                cv2.rectangle(img, (fin.p1[0], fin.p1[1]), (fin.p2[0], fin.p2[1]),
                              (0, 255, 0), 2)
        else:
            if tracked is not None:
                tracked.inc_lost()
                if tracked.get_lost_cnt() > 20:
                    tracked.mark_lost(datetime.datetime.now())
                    print(tracked.to_string())
                    tracked = None
        if args.imshow:
            cv2.imshow("test", img)
        if args.fps:
            print("FPS:", 1.0 / (time.time() - start_time))
        img = camera.capture_image()


if __name__ == "__main__":
    parser = init_arg_parse()
    args = parser.parse_args()
    # cam = VideoUtils.CameraMock('/Users/petr/Desktop/test2.mp4')
    cam = Camera.Camera()
    try:
        if args.bb_dist == 0:
            writer = VideoUtils.VideoWriter("/home/pi/Desktop/out/test_out.avi", (480, 480), 30.0)
            try:
                __unused__old_main(cam, args)
            finally:
                writer.close()

        else:
            alt_main(cam, args)
    finally:
        cam.close()

import argparse

import cv2
import imutils
# import Camera
import numpy as np

import Tracking
import VideoUtils

writer = None


def init_arg_parse():
    parser = argparse.ArgumentParser(description="MUL project")
    parser.add_argument("--video", required=True, dest='video_path', type=str)
    parser.add_argument("--area", required=True, dest='min_area', type=int)
    parser.add_argument("--tracker", default='kcf', dest='tracker', type=str)
    parser.add_argument("--enable_imshow", dest='imshow', default=False, action='store_true')
    parser.add_argument("--bb_dist", dest='bb_dist', default=0, type=float)
    return parser


def main(camera, args):
    detector = Tracking.ChangeDetector(camera.capture_image(), (args.min_area, args.min_area * 3), 480)
    det = Tracking.PersonDetector()
    searching = True
    tracker = None
    hog_fail_cnt = 0
    while True:
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
        if key == ord('q'):
            break


class ChangeDetector:
    def __init__(self, reference_img, thresh=5):
        gray = self.prepare_img(reference_img)
        self.avg_img = gray.copy().astype("float")
        self.thresh = thresh

    def detect_change(self, img):
        gray = self.prepare_img(img)
        cv2.accumulateWeighted(gray, self.avg_img, 0.5)
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg_img))
        cv2.imshow("delta", frame_delta)

        thresh = cv2.threshold(frame_delta, self.thresh, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        cv2.imshow("aaaa", thresh)
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        bbs = []
        for c in contours:
            bbs.append(cv2.boundingRect(c))

        return bbs

    def prepare_img(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray, (21, 21), 0)


def eucl_dist(a, b):
    return np.sqrt(pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2))


class BoundingBox:
    p1: np.array
    p2: np.array
    center: np.array

    @staticmethod
    def create_cv(bb):
        result = BoundingBox()
        result.p1 = np.asarray([bb[0], bb[1]])
        result.p2 = np.asarray([bb[0] + bb[2], bb[1] + bb[3]])
        result.center = (result.p1 + result.p2) / 2
        return result

    @staticmethod
    def create_points(p1, p2):
        result = BoundingBox()
        result.p1 = p1
        result.p2 = p2
        result.center = (result.p1 + result.p2) / 2
        return result

    def combine(self, bb):
        p1 = np.asarray([min(self.p1[0], bb.p1[0]), min(self.p1[1], bb.p1[1])])
        p2 = np.asarray([max(self.p2[0], bb.p2[0]), max(self.p2[1], bb.p2[1])])
        return BoundingBox.create_points(p1, p2)

    def distance(self, other):
        return min(eucl_dist(self.p1, other.p1), eucl_dist(self.p2, other.p2),
                   eucl_dist(self.p1, other.p2), eucl_dist(self.p2, other.p1))

    def width(self):
        return self.p2[0] - self.p1[0]

    def height(self):
        return self.p2[1] - self.p1[1]

    def area(self):
        return self.width() * self.height()


def alt_main(camera, args):
    img = camera.capture_image()
    detector = ChangeDetector(img, 5)
    while img is not None:
        bbs = detector.detect_change(img)
        if len(bbs) > 0:
            boxes = [BoundingBox.create_cv(bbs[0])]
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
        if args.imshow:
            cv2.imshow("test", img)
            cv2.waitKey(1)
        img = camera.capture_image()


if __name__ == "__main__":
    parser = init_arg_parse()
    args = parser.parse_args()
    cam = VideoUtils.CameraMock('/Users/petr/Desktop/test2.mp4')
    try:
        if args.bb_dist == 0:
            writer = VideoUtils.VideoWriter("/home/pi/Desktop/out/test_out.avi", (480, 480), 30.0)
            try:
                main(cam, args)
            finally:
                writer.close()

        else:
            alt_main(cam, args)
    finally:
        cam.close()

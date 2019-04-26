import cv2
import imutils

from geometryutils import BoundingBox


class TrackedObject:
    def __init__(self, start_time, video_location=None):
        self.__bb = None
        self.__lost_time = None
        self.__start_time = start_time
        self.__lost_frame_cnt = 0
        if video_location is not None:
            self.__video_location = video_location

    def set_last_position(self, bb: BoundingBox):
        self.__bb = bb

    def get_last_position(self):
        return self.__bb

    def inc_lost(self):
        self.__lost_frame_cnt += 1

    def reset_lost(self):
        self.__lost_frame_cnt = 0

    def get_lost_cnt(self):
        return self.__lost_frame_cnt

    def mark_lost(self, lost_time):
        self.__lost_time = lost_time

    def get_video_location(self):
        return self.__video_location

    def get_times(self):
        return self.__start_time, self.__lost_time

    def to_string(self):
        return "Appeared: " + str(self.__start_time) + ", lost: " + str(self.__lost_time)


class ChangeLocator:
    def __init__(self, reference_img, thresh=5):
        gray = self.prepare_img(reference_img)
        self.avg_img = gray.copy().astype("float")
        self.thresh = thresh

    def detect_change(self, img):
        gray = self.prepare_img(img)
        cv2.accumulateWeighted(gray, self.avg_img, 0.5)
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg_img))

        thresh = cv2.threshold(frame_delta, self.thresh, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cv2.imshow("t", thresh)

        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        bbs = []
        for c in contours:
            bbs.append(BoundingBox.create_cv(cv2.boundingRect(c)))

        return bbs

    def prepare_img(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray, (13, 13), 0)


#######################################
############### UNUSED ################
#######################################
class ChangeDetector:
    def __init__(self, reference_img, area_limits: (int, int), resize, thresh=5):
        self.resize = resize
        gray = self.prepare_img(reference_img)
        self.avg_img = gray.copy().astype("float")
        self.area_limits = area_limits
        self.thresh = thresh

    def detect(self, img):
        gray = self.prepare_img(img)
        cv2.accumulateWeighted(gray, self.avg_img, 0.5)
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg_img))

        thresh = cv2.threshold(frame_delta, self.thresh, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        max_area = 0
        bounding_box = None
        for c in contours:
            area = cv2.contourArea(c)
            (x, y, w, h) = cv2.boundingRect(c)

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if self.area_limits[0] < area < self.area_limits[1] and w * 3.0 > h > 1.5 * w and area > max_area:
                bounding_box = (x, y, w, h)
                max_area = area
        cv2.imshow("b", thresh)
        if bounding_box is not None:
            return True, bounding_box

        return False, None

    def prepare_img(self, img):
        img = imutils.resize(img, width=self.resize)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray, (21, 21), 0)


class PersonDetector:
    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, img, sub_area=None):
        if sub_area is not None:
            (x, y, w, h) = sub_area
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            img = img[y:y + h, x:x + w]
        rects, weights = self.hog.detectMultiScale(img, winStride=(8, 8),
                                                   padding=(20, 20), scale=1.05, hitThreshold=0.1)
        if sub_area is not None:
            for rect in rects:
                rect[0] += x
                rect[1] += y
        return rects, weights


OPENCV_OBJECT_TRACKERS = {
    "csrt": cv2.TrackerCSRT_create,
    "kcf": cv2.TrackerKCF_create,
    "boosting": cv2.TrackerBoosting_create,
    "tld": cv2.TrackerTLD_create,
    "medianflow": cv2.TrackerMedianFlow_create,
    "mosse": cv2.TrackerMOSSE_create
}


class PersonTracker:
    def __init__(self, tracker_name: str, img, init_bb, resize):
        self.tracker = OPENCV_OBJECT_TRACKERS[tracker_name]()
        self.tracker.init(img, init_bb)
        self.resize = resize

    def update(self, img):
        img = imutils.resize(img, width=self.resize)
        return self.tracker.update(img)


class FaceDetector:
    def __init__(self):
        self.detector = cv2.CascadeClassifier('/Users/petr/Desktop/haarcascade_frontalface_alt.xml')

    def detect(self, img, sub_area=None):
        if sub_area is not None:
            (x, y, w, h) = sub_area
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            img = img[y:y + h, x:x + w]

        rects = self.detector.detectMultiScale(img)
        if sub_area is not None:
            for rect in rects:
                rect[0] += x
                rect[1] += y
        return rects

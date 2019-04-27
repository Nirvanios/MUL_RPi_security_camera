import argparse
import datetime
import math
import random
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from queue import Queue

import cv2
import numpy as np

import mulconfig
import npcamera
import tracking
import videoutils
from Remote_server.Sender import Sender
from buzzer import Buzzer
from emailsender import Email
from logger import logger_instance as l, LogLevel


class QueueItem(Enum):
    """
    Types of messages allowed in queue.
    """
    # str with file name
    file_start = 1
    # tuple of image and bounding box
    image = 2
    # tuple of start and end time
    file_end = 3


class SaveThreadState(Enum):
    waiting = 1
    saving_imgs = 2


# queue for communication between detection and file handling thread
saving_queue = Queue()


def combine_boxes(boxes, config):
    """
    Reduce bounding boxes to bigger ones.
    """
    change = True
    while change:
        change = False
        for box in boxes:
            for box2 in boxes:
                if box == box2:
                    continue
                if box.distance(box2) < config.get_value("cv.bb_max_distance"):
                    boxes[boxes.index(box)] = box.combine(box2)
                    boxes.remove(box2)
                    change = True
                    break
    return boxes


def find_person(boxes, config):
    """
    Find bounding box most likely to contain a person.
    :return: bounding box if conditions are met, otherwise None
    """
    boxes = combine_boxes(boxes, config)
    fin = None
    for box in boxes:
        ratio = box.width() / box.height()
        if config.get_value("cv.min_area") < box.area() < config.get_value("cv.max_area") \
                and config.get_value("cv.min_ratio") < ratio < config.get_value("cv.max_ratio"):
            if fin is None:
                fin = box
                continue
            if box.area() > fin.area():
                fin = box
    return fin


def detect_and_notify(config: mulconfig.Config):
    """
    Periodically detect changes in video stream from camera. Notify other thread using saving_queue.
    """
    camera = npcamera.Camera((config.get_value("cv.resolution.width"), config.get_value("cv.resolution.height")))
    locator = tracking.ChangeLocator(camera.capture_image())
    tracked = None
    cnt = 0
    while True:
        img = camera.capture_image()
        person_bb = find_person(locator.detect_change(img), config)
        if person_bb is not None:
            if tracked is None:
                tracked = tracking.TrackedObject(datetime.datetime.now())
                saving_queue.put((QueueItem.file_start, str(cnt) + ".mp4"))
                l.log(LogLevel.DEBUG, "Creating tracker")
                cnt += 1
            else:
                tracked.reset_lost()
                l.log(LogLevel.DEBUG, "Resetting tracker")
            saving_queue.put((QueueItem.image, (img, person_bb)))
        else:
            if tracked is not None:
                tracked.inc_lost()
                saving_queue.put((QueueItem.image, (img, None)))
                if tracked.get_lost_cnt() > config.get_value("cv.lost_frames_max"):
                    l.log(LogLevel.DEBUG, "Lost object")
                    tracked.mark_lost(datetime.datetime.now())
                    saving_queue.put((QueueItem.file_end, (tracked.get_times())))
                    tracked = None


def acquire_and_save(config: mulconfig.Config, on_saving_done):
    """
    Periodically reads data from saving_queue and saves it into file.
    Calls on_saving_done(file_name, time_start, time_end) when saving is finished.
    """
    state = SaveThreadState.waiting
    writer = None
    frame_cnt = 0
    resolution = config.get_value("cv.resolution.width"), config.get_value("cv.resolution.height")
    bbs = []
    thread_pool = ThreadPoolExecutor(max_workers=2)
    buzzer = Buzzer()
    while True:
        (item_type, item) = saving_queue.get()
        if state == SaveThreadState.waiting:
            if item_type is QueueItem.file_start:
                writer = videoutils.VideoWriter(config.get_value("save_location") + item, resolution, 7.0)
                state = SaveThreadState.saving_imgs
                l.log(LogLevel.DEBUG, "Start saving")
                buzzer.start_alarm()
            else:
                l.log(LogLevel.ERROR,
                      "Invalid item type in saving thread. State: " + state.name + " item type: " + item_type.name)
        if state == SaveThreadState.saving_imgs:
            if item_type is QueueItem.image:
                img = item[0]
                if item[1] is not None:
                    bbs.append((item[1], frame_cnt))
                    bb = item[1]
                    cv2.rectangle(img, (bb.p1[0], bb.p1[1]), (bb.p2[0], bb.p2[1]), (0, 255, 0), 2)
                writer.write_frame(img)
                frame_cnt += 1
            elif item_type is QueueItem.file_end:
                writer.close()
                state = SaveThreadState.waiting
                thread_pool.submit(on_saving_done, config, writer.dest_path, item[0], item[1], bbs[:])
                l.log(LogLevel.DEBUG, "Saving finished to:" + writer.dest_path)
                buzzer.stop_alarm()
                frame_cnt = 0
                bbs.clear()
            else:
                l.log(LogLevel.ERROR,
                      "Invalid item type in saving thread. State: " + state.name + " item type: " + item_type.name)


def on_saving_done(config: mulconfig.Config, file_path: str, start_time, end_time, bbs):
    l.log(LogLevel.DEBUG, "Saving done, notifying...")
    time_duration = str(start_time.strftime("%Y-%m-%d %H:%M:%S")) + " - " + str(end_time.strftime("%Y-%m-%d %H:%M:%S"))
    email_sender = Email(config.get_value("e-mail.e-mail"),
                         config.get_value("e-mail.password"),
                         config.get_value("e-mail.smtp"),
                         config.get_value("e-mail.port"))
    file_sender = Sender()
    random.seed()
    try:
        with open(file_path, "rb") as file:
            file_sender.send_standard_file(config.get_value("file_server.ipv4"),
                                           config.get_value("file_server.port"),
                                           time_duration + ".mp4",
                                           file.read())
    except socket.error as e:
        l.log(LogLevel.ERROR, "Send to server has failed. " + e.strerror)
    images = []
    video = cv2.VideoCapture(file_path)
    bbs_count = len(bbs) - 1
    print(bbs_count)
    print(bbs)
    if bbs_count > -1:
        for _ in range(2):
            frame = random.randrange(bbs_count)
            video.set(cv2.CAP_PROP_POS_FRAMES, bbs[frame][1])
            state, image = video.read()
            state, jpeg_image = cv2.imencode(".jpeg", image, (cv2.IMWRITE_JPEG_QUALITY, 90))
            images.append(jpeg_image.tobytes())
    try:
        email_sender.send_email(config.get_value("e-mail.e-mail"), date_time=time_duration, jpg_images=images)
    except Exception:
        l.log(LogLevel.ERROR, "E-mail sending has failed.")


def init_arg_parse():
    parser = argparse.ArgumentParser(description="MUL project")
    parser.add_argument("--config", dest='show_config', action='store_true')
    return parser


def main():
    parser = init_arg_parse()
    args = parser.parse_args()
    config = mulconfig.Config('./config.json')
    if args.show_config:
        width, height = config.get_value("cv.resolution.width"), config.get_value("cv.resolution.height")
        camera = npcamera.Camera((width, height))
        img = camera.capture_image()
        to_show = np.copy(img)
        min_ratio = config.get_value("cv.min_ratio")
        half_width = width // 2
        cv2.rectangle(to_show, (0, 0), (int(half_width * min_ratio), half_width), (0, 255, 0), 2)
        cv2.imshow("min_ratio", to_show)
        to_show = np.copy(img)
        max_ratio = config.get_value("cv.max_ratio")
        cv2.rectangle(to_show, (0, 0), (int(half_width * max_ratio), half_width), (0, 255, 0), 2)
        cv2.imshow("max_ratio", to_show)
        to_show = np.copy(img)
        ratio = (min_ratio + max_ratio) / 2
        min_area = config.get_value("cv.min_area")
        h = int(math.sqrt(min_area / ratio))
        w = int(h * ratio)
        cv2.rectangle(to_show, (0, 0), (w, h), (0, 255, 0), 2)
        cv2.imshow("min_area", to_show)
        to_show = np.copy(img)
        max_area = config.get_value("cv.max_area")
        h = int(math.sqrt(max_area / ratio))
        w = int(h * ratio)
        cv2.rectangle(to_show, (0, 0), (w, h), (0, 255, 0), 2)
        cv2.imshow("max_area", to_show)
        cv2.waitKey()
    else:
        detection_thread = threading.Thread(target=detect_and_notify, args=(config,))
        detection_thread.start()

        saving_thread = threading.Thread(target=acquire_and_save, args=(config, on_saving_done))
        saving_thread.start()
        saving_thread.join()
        detection_thread.join()


if __name__ == "__main__":
    main()

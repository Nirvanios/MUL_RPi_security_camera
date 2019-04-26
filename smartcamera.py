import datetime
import threading
from enum import Enum
from queue import Queue

import cv2

import mulconfig
import npcamera
import tracking
import videoutils
from logger import logger_instance as l, LogLevel


class QueueItem(Enum):
    # str with file name
    file_start = 1
    # tuple of image and bounding box
    image = 2
    # tuple of start and end time
    file_end = 3


class SaveThreadState(Enum):
    waiting = 1
    saving_imgs = 2


saving_queue = Queue()


def combine_boxes(boxes, config):
    change = True
    while change:
        change = False
        for box in boxes:
            for box2 in boxes:
                if box == box2:
                    continue
                if box.distance(box2) < config.get_value("bb_max_distance"):
                    boxes[boxes.index(box)] = box.combine(box2)
                    boxes.remove(box2)
                    change = True
                    break
    return boxes


def find_person(boxes, config):
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
    camera = npcamera.Camera((config.get_value("cv.resolution.width"), config.get_value("cv.resolution.height")))
    locator = tracking.ChangeLocator(camera.capture_image())
    tracked = None
    while True:
        img = camera.capture_image()
        person_bb = find_person(locator.detect_change(img))
        if person_bb is not None:
            if tracked is None:
                tracked = tracking.TrackedObject(datetime.datetime.now())
                saving_queue.put((QueueItem.file_start, "filename.mp4"))
            else:
                tracked.reset_lost()
            saving_queue.put((QueueItem.image, (img, person_bb)))
        else:
            if tracked is not None:
                tracked.inc_lost()
                saving_queue.put((QueueItem.image, (img, None)))
                if tracked.get_lost_cnt() > config.get_value("lost_frames_max"):
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
    resolution = config.get_value("cv.resolution.width"), config.get_value("cv.resolution.height")
    while True:
        (item_type, item) = saving_queue.get()
        if state == SaveThreadState.waiting and item_type is QueueItem.file_start:
            writer = videoutils.VideoWriter(config.get_value("save_location") + item, resolution, 12.0)
            state = SaveThreadState.saving_imgs
            l.log(LogLevel.DEBUG, "Start saving")
        else:
            l.log(LogLevel.ERROR,
                  "Invalid item type in saving thread. State: " + state.name + " item type: " + item_type.name)
        if state == SaveThreadState.saving_imgs:
            if item_type is QueueItem.image:
                img = item[0]
                if item[2] is not None:
                    (x1, y1, x2, y2) = item[2]
                    cv2.rectangle((x1, y1), (x2, y2), (0, 255, 0), 2)
                writer.write_frame(img)
                l.log(LogLevel.DEBUG, "Writing frame")
            elif item_type is QueueItem.file_end:
                writer.close()
                state = SaveThreadState.waiting
                on_saving_done(writer.dest_path, item)
                l.log(LogLevel.DEBUG, "Saving finished to:" + writer.dest_path)
            else:
                l.log(LogLevel.ERROR,
                      "Invalid item type in saving thread. State: " + state.name + " item type: " + item_type.name)


def on_saving_done(file_path: str, start_time, end_time):
    l.log(LogLevel.DEBUG, "Saving done, notifying...")


def main():
    config = mulconfig.Config('./config.json')
    detection_thread = threading.Thread(target=detect_and_notify, args=(config,))
    detection_thread.start()

    saving_thread = threading.Thread(target=acquire_and_save, args=(config, on_saving_done))
    saving_thread.start()
    saving_thread.join()
    detection_thread.join()


if __name__ == "__main__":
    main()

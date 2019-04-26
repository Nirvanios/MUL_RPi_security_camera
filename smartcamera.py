import threading
from enum import Enum
from queue import Queue

import cv2

import mulconfig
import videoutils
from logger import logger_instance as l, LogLevel


class QueueItem(Enum):
    file_start = 1
    image = 2
    file_end = 3


class SaveThreadState(Enum):
    waiting = 1
    saving_imgs = 2


img_queue = Queue()


def detect_and_notify(config: mulconfig.Config):
    pass


def acquire_and_save(config: mulconfig.Config, on_saving_done):
    state = SaveThreadState.waiting
    writer = None
    resolution = config.get_value("cv.resolution.width"), config.get_value("cv.resolution.height")
    while True:
        (item_type, item) = img_queue.get()
        if state == SaveThreadState.waiting and item_type is QueueItem.file_start:
            writer = videoutils.VideoWriter(config.get_value("save_location") + item, resolution, 12.0)
            state = SaveThreadState.saving_imgs
        else:
            l.log(LogLevel.ERROR,
                  "Invalid item type in saving thread. State: " + state.name + " item type: " + item_type.name)
        if state == SaveThreadState.saving_imgs:
            if item_type is QueueItem.image:
                img = item[0]
                (x1, y1, x2, y2) = item[2]
                cv2.rectangle((x1, y1), (x2, y2), (0, 255, 0), 2)
                writer.write_frame(img)
            elif item_type is QueueItem.file_end:
                writer.close()
                state = SaveThreadState.waiting
                on_saving_done(writer.dest_path)
            else:
                l.log(LogLevel.ERROR,
                      "Invalid item type in saving thread. State: " + state.name + " item type: " + item_type.name)


def main():
    config = mulconfig.Config('./config.json')
    detection_thread = threading.Thread(target=detect_and_notify, args=(config,))
    detection_thread.start()

    saving_thread = threading.Thread(target=acquire_and_save, args=(config,))
    saving_thread.start()
    saving_thread.join()
    detection_thread.join()


if __name__ == "__main__":
    main()

import time
from typing import Tuple

import numpy as np
import picamera


class Camera:
    """
    Class for taking pictures with RPi camera
    """

    def __init__(self, resolution: Tuple[int, int] = (640, 480)):
        """
        Initializes camera, and waits 2s for it to be ready.
        :param resolution: Resolution of captured images.
        """
        self.__camera = picamera.PiCamera()
        self.__camera.resolution = resolution
        time.sleep(1)

    def capture_image(self):
        """
        Captures bgr image and returns it as numpy array
        :return: numpy array with image.
        """
        image_size = self.__camera.resolution[::-1]
        capture_width = (image_size[0] + 31) // 32 * 32
        capture_height = (image_size[1] + 15) // 16 * 16
        image = np.empty((capture_width, capture_height, 3), dtype=np.uint8)
        self.__camera.capture(image, format="bgr", use_video_port=True)
        image = image[:image_size[0], :image_size[1], :]
        return image

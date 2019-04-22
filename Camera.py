import io
import time
import picamera
import numpy as np
from typing import Tuple


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
        self.__resolution = resolution
        self.__camera.resolution = resolution
        time.sleep(2)

    def capture_image(self):
        """
        Captures bgr image and returns it as numpy array
        :return: numpy array with image.
        """
        stream = io.BytesIO()
        self.__camera.capture(stream, format="bgr", use_video_port=True)
        fwidth = (self.__resolution[0] + 31) // 32 * 32
        fheight = (self.__resolution[1] + 15) // 16 * 16
        image = np.fromstring(stream.getvalue(), dtype=np.uint8) \
                    .reshape((fheight, fwidth, 3))[:self.__resolution[0], :self.__resolution[1], :]
        return image

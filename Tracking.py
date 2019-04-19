import cv2


class CameraMock:
    def __init__(self, file_path):
        self.file_path = file_path

    def open(self):
        self.cap = cv2.VideoCapture(self.file_path)

    def close(self):
        self.cap.release()

    def capture_image(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            return frame
        else:
            return None

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

    def is_running(self):
        return self.cap.isOpened()

    def get_resolution(self):
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height


class VideoWriter:
    def __init__(self, dest_path, resolution, fps):
        self.dest_path = dest_path
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(dest_path, fourcc, fps, resolution)

    def write_frame(self, frame):
        self.out.write(frame)

    def close(self):
        self.out.release()


class Tracker:
    def __init__(self):
        self.tr = cv2.TrackerCSRT_create()

    def track(self, frame):
        return self.tr.update(frame)

import cv2


class VideoWriter:
    def __init__(self, dest_path, resolution, fps):
        self.dest_path = dest_path
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(dest_path, fourcc, fps, resolution)

    def write_frame(self, frame):
        self.out.write(frame)

    def close(self):
        self.out.release()

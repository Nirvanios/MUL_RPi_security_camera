import argparse

import cv2

import Tracking


def init_arg_parse():
    parser = argparse.ArgumentParser(description="MUL project")
    return parser


def main():
    parser = init_arg_parse()
    args = parser.parse_args()

    camera = Tracking.CameraMock('/Users/petr/Desktop/test.mp4')
    camera.open()
    try:
        img = camera.capture_image()
        cnt = 0
        while img is not None:
            cv2.imshow("man", img)
            cnt += 1
            print("Frame: " + str(cnt))
            cv2.waitKey()
            img = camera.capture_image()
    finally:
        camera.close()


if __name__ == "__main__":
    main()

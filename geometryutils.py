import numpy as np


def euclidean_distance(a, b):
    return np.sqrt(pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2))


class BoundingBox:

    @staticmethod
    def create_cv(bb):
        result = BoundingBox()
        result.p1 = np.asarray([bb[0], bb[1]])
        result.p2 = np.asarray([bb[0] + bb[2], bb[1] + bb[3]])
        result.center = (result.p1 + result.p2) / 2
        return result

    @staticmethod
    def create_points(p1, p2):
        result = BoundingBox()
        result.p1 = p1
        result.p2 = p2
        result.center = (result.p1 + result.p2) / 2
        return result

    def combine(self, bb):
        p1 = np.asarray([min(self.p1[0], bb.p1[0]), min(self.p1[1], bb.p1[1])])
        p2 = np.asarray([max(self.p2[0], bb.p2[0]), max(self.p2[1], bb.p2[1])])
        return BoundingBox.create_points(p1, p2)

    def distance(self, other):
        return min(euclidean_distance(self.p1, other.p1), euclidean_distance(self.p2, other.p2),
                   euclidean_distance(self.p1, other.p2), euclidean_distance(self.p2, other.p1))

    def width(self):
        return self.p2[0] - self.p1[0]

    def height(self):
        return self.p2[1] - self.p1[1]

    def area(self):
        return self.width() * self.height()

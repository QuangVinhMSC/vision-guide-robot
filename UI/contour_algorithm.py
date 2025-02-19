import cv2
import numpy as np

class ContourProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.template_gray = cv2.imread(image_path, 0)
        self.template_color = cv2.cvtColor(self.template_gray, cv2.COLOR_GRAY2BGR)
        _, self.template_edges = cv2.threshold(self.template_gray, 90, 255, cv2.THRESH_BINARY)
        self.contours_template, _ = cv2.findContours(self.template_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.min_perimeter = 100
        self.contours_template = [cv2.approxPolyDP(cnt, epsilon=8, closed=True) for cnt in self.contours_template
                                  if cv2.arcLength(cnt, closed=True) > self.min_perimeter]

        print(f'Số lượng contours sau khi lọc: {len(self.contours_template)}')

    def shrink_contour(self, contour, scale):
        """ Tạo contour nhỏ hơn dựa trên scale factor """
        M = cv2.moments(contour)
        if M["m00"] == 0:
            return contour

        cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
        new_contour = []
        for point in contour:
            x, y = point[0]
            x_new = cx + scale * (x - cx)
            y_new = cy + scale * (y - cy)
            new_contour.append([[int(x_new), int(y_new)]])

        return np.array(new_contour, dtype=np.int32)

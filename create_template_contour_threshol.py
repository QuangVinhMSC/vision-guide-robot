import cv2
import numpy as np

class ContourEditor:
    def __init__(self, image_path):
        self.template_gray = cv2.imread(image_path, 0)
        self.template_color = cv2.cvtColor(self.template_gray, cv2.COLOR_GRAY2BGR)
        _, self.template_edges = cv2.threshold(self.template_gray, 90, 255, cv2.THRESH_BINARY)
        self.contours_template, _ = cv2.findContours(self.template_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.min_perimeter = 100
        self.contours_template = [cv2.approxPolyDP(cnt, epsilon=8, closed=True) for cnt in self.contours_template if cv2.arcLength(cnt, closed=True) > self.min_perimeter]
        print(f'Số lượng contours sau khi lọc: {len(self.contours_template)}')

        self.selected_contour = None
        self.contour_inner = None
        self.selected_point_idx = None
        self.contour_selected = False
        self.scale_factor = 0.8  # Tỷ lệ thu nhỏ contour
        
        cv2.namedWindow('Edit Contour', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Edit Contour', 800, 800)
        cv2.setMouseCallback('Edit Contour', self.select_contour)
        self.update_display()

    def shrink_contour(self, contour, scale_factor=0.8):
        """ Tạo một contour nhỏ hơn bằng cách co về trọng tâm """
        M = cv2.moments(contour)
        if M["m00"] == 0:
            return contour.copy()
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        contour_scaled = []
        for point in contour:
            px, py = point[0]
            new_x = int(cx + scale_factor * (px - cx))
            new_y = int(cy + scale_factor * (py - cy))
            contour_scaled.append([[new_x, new_y]])
        return np.array(contour_scaled, dtype=np.int32)

    def update_display(self):
        display = self.template_color.copy()
        cv2.drawContours(display, self.contours_template, -1, (255, 255, 255), 1)

        if self.selected_contour is not None:
            cv2.drawContours(display, [self.selected_contour], -1, (0, 0, 255), 2)
            for point in self.selected_contour:
                x, y = point[0]
                cv2.circle(display, (x, y), 5, (255, 0, 0), -1)  # Chấm tròn xanh dương

        if self.contour_inner is not None:
            cv2.drawContours(display, [self.contour_inner[:,:,0:2]], -1, (0, 255, 0), 2)  # Contour nhỏ với màu xanh lá
            for point in self.contour_inner[:,:,0:2]:
                x, y = point[0]
                cv2.circle(display, (x, y), 3, (0, 255, 255), -1)  # Chấm tròn vàng
        cv2.imshow('Edit Contour', display)

    def select_contour(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if not self.contour_selected:
                for cnt in self.contours_template:
                    if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:
                        self.selected_contour = cnt
                        self.contour_inner = self.shrink_contour(cnt, self.scale_factor)  # Tạo contour nhỏ hơn
                        self.contour_inner = cv2.approxPolyDP(self.contour_inner, epsilon=8, closed=True)
                        self.contour_inner = np.concatenate((self.contour_inner, np.zeros((self.contour_inner.shape[0], 1, 1), dtype=self.contour_inner.dtype)), axis=2)
                        print(self.contour_inner[:,:,0:2])
                        self.contour_selected = True
                        print("Contour đã chọn!")
                        break
            if self.selected_contour is not None:
                for i, point in enumerate(self.selected_contour):
                    px, py = point[0]
                    if abs(px - x) < 5 and abs(py - y) < 5:
                        self.selected_point_idx = i
                        print(f"Điểm đã chọn trên contour gốc: {px}, {py}")
                        break
            if self.contour_inner is not None:
                for i, point in enumerate(self.contour_inner[:,:,0:2]):
                    px, py = point[0]
                    if abs(px - x) < 5 and abs(py - y) < 5:
                        self.selected_point_idx = i
                        print(f"Điểm đã chọn trên contour nhỏ: {px}, {py}")
                        break
        self.update_display()

    def run(self):
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('p'):
                self.contour_selected = False
                self.selected_contour = None
                self.contour_inner = None
                self.selected_point_idx = None
                print("Có thể chọn lại contour mới!")
                self.update_display()
            elif key in [ord('w'), ord('a'), ord('s'), ord('d')] and self.selected_point_idx is not None and self.selected_contour is not None:
                if key == ord('w'):
                    self.selected_contour[self.selected_point_idx][0][1] -= 1
                elif key == ord('s'):
                    self.selected_contour[self.selected_point_idx][0][1] += 1
                elif key == ord('a'):
                    self.selected_contour[self.selected_point_idx][0][0] -= 1
                elif key == ord('d'):
                    self.selected_contour[self.selected_point_idx][0][0] += 1
                self.update_display()
            elif key in [ord('i'), ord('j'), ord('k'), ord('l'),ord('u'),ord('h')] and self.selected_point_idx is not None and self.contour_inner is not None:
                if key == ord('i'):
                    self.contour_inner[:,:,0:2][self.selected_point_idx][0][1] -= 1
                elif key == ord('k'):
                    self.contour_inner[:,:,0:2][self.selected_point_idx][0][1] += 1
                elif key == ord('j'):
                    self.contour_inner[:,:,0:2][self.selected_point_idx][0][0] -= 1
                elif key == ord('l'):
                    self.contour_inner[:,:,0:2][self.selected_point_idx][0][0] += 1
                elif key == ord('u'):
                    self.contour_inner[self.selected_point_idx][0][2] -= 1
                    print(self.contour_inner[self.selected_point_idx][0][2])
                elif key == ord('h'):
                    self.contour_inner[self.selected_point_idx][0][2] += 1
                    print(self.contour_inner[self.selected_point_idx][0][2])
                self.update_display()
            elif key == ord('o') and self.selected_contour is not None:
                print("Contour đã được lưu!")
        cv2.destroyAllWindows()

if __name__ == "__main__":
    editor = ContourEditor('/home/vinhdq/I&C_PROJECT/image/captured_image.png')
    editor.run()
    np.save('/home/vinhdq/I&C_PROJECT/temp_contour/selected_contour.npy', editor.selected_contour)
    np.save('/home/vinhdq/I&C_PROJECT/temp_contour/contour_inner.npy', editor.contour_inner)
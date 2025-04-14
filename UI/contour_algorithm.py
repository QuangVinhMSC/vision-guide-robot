import cv2
import numpy as np
import pyclipper
from camera import ContourDetector

class ContourProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.template_gray = cv2.imread(image_path, 0)
        self.template_color = cv2.cvtColor(self.template_gray, cv2.COLOR_GRAY2BGR)
        self.epsilon = 1
        self.offset_list = None
        self.threshol_editor((90,150))
    def take_a_image(self):
        self.matcher = ContourDetector()
        self.template_gray = self.matcher.capture_single_shot()
        self.template_color = cv2.cvtColor(self.template_gray, cv2.COLOR_GRAY2BGR)
        self.matcher.rm_camera()
    def threshol_editor(self, threshol=(90,150)):
        _, self.template_edges = cv2.threshold(self.template_gray, threshol[0], threshol[1], cv2.THRESH_BINARY)
        self.contours_template_raw, _ = cv2.findContours(self.template_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)      
        print(len(self.contours_template_raw))
        self.min_perimeter = 100
        self.contours_template = [cv2.approxPolyDP(cnt, epsilon=self.epsilon, closed=True) for cnt in self.contours_template_raw
                                  if cv2.arcLength(cnt, closed=True) > self.min_perimeter]
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

    def contour_offset(self, contour, offset):
        contour = tuple(map(tuple, contour.reshape(contour.shape[0], 2)))
        pco = pyclipper.PyclipperOffset()
        pco.AddPath(contour, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        solution = pco.Execute(offset)[0]
        offsetted_contour = []
        for point in solution:
            offsetted_contour.append([point])
        return np.array(offsetted_contour, dtype=np.int32)
    def simplify_contour_min_distance(self,contour, radius):
        """
        Đơn giản hóa contour bằng cách chỉ giữ lại các điểm có khoảng cách tối thiểu với nhau
        
        Tham số:
            contour: numpy array có shape (N, 1, 2) - các điểm của contour
            radius: int - khoảng cách tối thiểu giữa các điểm
            
        Trả về:
            simplified_contour: numpy array - contour đã được đơn giản hóa
        """
        if len(contour) <= 2:
            return contour.copy()
        
        # Chuyển đổi contour về dạng (N, 2) để dễ xử lý
        points = contour.squeeze(1)
        
        # Khởi tạo danh sách điểm kết quả với điểm đầu tiên
        simplified_points = [points[0]]
        
        # Điểm tham chiếu để so sánh khoảng cách
        reference_point = points[0]
        
        for point in points[1:]:
            # Tính khoảng cách Euclidean từ điểm hiện tại đến điểm tham chiếu
            distance = np.linalg.norm(point - reference_point)
            
            # Nếu khoảng cách >= radius, thêm điểm này vào kết quả
            # và cập nhật điểm tham chiếu
            if distance >= radius:
                simplified_points.append(point)
                reference_point = point
        
        # Đảm bảo có ít nhất 2 điểm trong contour
        if len(simplified_points) == 1:
            simplified_points.append(points[-1])
        
        # Chuyển đổi kết quả về dạng contour (N, 1, 2)
        simplified_contour = np.array(simplified_points).reshape(-1, 1, 2)
        
        return simplified_contour

    def calculate_offset(self, contour, simplified_contour, offset_distance, window_size=5, point=None, individual_offset=None):
        """
        Tính offset với pháp tuyến được tính từ nhiều điểm xung quanh.
        Nếu chỉ định `point` và `individual_offset`, điểm đó sẽ dùng giá trị offset riêng.

        Tham số:
            contour: numpy array shape (N, 1, 2) - contour gốc
            simplified_contour: numpy array shape (M, 1, 2) - contour đã đơn giản hóa
            offset_distance: float - khoảng cách offset mặc định
            window_size: int - số điểm mỗi bên dùng để tính pháp tuyến (tổng điểm = 2*window_size + 1)
            point: int (tùy chọn) - chỉ số điểm trong simplified_contour cần thay đổi offset
            individual_offset: float (tùy chọn) - giá trị offset riêng cho điểm được chọn
            offset_list: list (tùy chọn) - danh sách các giá trị offset cho từng điểm (có độ dài bằng số điểm trong contour)

        Trả về:
            offset_contour: numpy array shape (M, 1, 2) dtype=np.int32
        """
        points = contour.squeeze(1)
        simplified_points = simplified_contour.squeeze(1)
        
        # Nếu không có offset_list được truyền vào, khởi tạo offset_list với giá trị mặc định
        if self.offset_list is None:
            self.offset_list = [offset_distance] * len(simplified_points)
        if point is None:
            self.offset_list = [offset_distance] * len(simplified_points)
        # Kiểm tra nếu có chỉ định điểm riêng
        if point is not None:
            if point < 0 or point >= len(simplified_points):
                raise ValueError("Chỉ số điểm không hợp lệ")
            if individual_offset is None:
                raise ValueError("Phải cung cấp individual_offset khi chỉ định point")
            
            # Cập nhật giá trị offset cho điểm được chỉ định trong offset_list
            self.offset_list[point] = individual_offset

        # Tìm chỉ số các điểm simplified trong contour gốc
        indices = [np.argmin(np.linalg.norm(points - sp, axis=1)) for sp in simplified_points]
        
        offset_result = []
        
        for i, idx in enumerate(indices):
            # Tập hợp các điểm lân cận trong cửa sổ
            neighbor_indices = []
            for k in range(-window_size, window_size + 1):
                neighbor_idx = (idx + k) % len(points)
                neighbor_indices.append(neighbor_idx)
            
            # Tính trung bình các vector pháp tuyến
            avg_normal = np.zeros(2)
            for j in range(1, len(neighbor_indices)):
                prev_idx = neighbor_indices[j-1]
                curr_idx = neighbor_indices[j]
                tangent = points[curr_idx] - points[prev_idx]
                normal = np.array([-tangent[1], tangent[0]])
                norm = np.linalg.norm(normal)
                if norm > 1e-6:  # Tránh chia cho 0
                    avg_normal += normal / norm
            
            # Chuẩn hóa vector pháp tuyến trung bình
            norm_avg = np.linalg.norm(avg_normal)
            if norm_avg > 1e-6:
                avg_normal = avg_normal / norm_avg
            
            # Lấy giá trị offset từ offset_list
            current_offset = self.offset_list[i]  # Sử dụng giá trị trong offset_list cho điểm i
            
            # Tính điểm offset
            offset_point = simplified_points[i] + avg_normal * current_offset
            offset_point = np.round(offset_point).astype(np.int32)
            offset_result.append([offset_point])
        
        return np.array(offset_result, dtype=np.int32)

import cv2
import numpy as np
import time
from pypylon import pylon

class ContourMatcher:
    def __init__(self, template_path, inner_contour_path):
        self.template_path = template_path
        self.inner_contour_path = inner_contour_path
        self.camera = self.create_camera()
        self.load_templates()
    
    def create_camera(self):
        TLFactory = pylon.TlFactory.GetInstance()
        devices = TLFactory.EnumerateDevices()
        if len(devices) == 0:
            raise Exception("No camera found")
        camera = pylon.InstantCamera(TLFactory.CreateDevice(devices[0]))
        camera.Open()
        camera.PixelFormat.SetValue("Mono8")
        camera.Width.SetValue(2440)
        camera.Height.SetValue(2048)
        return camera

    def capture_single_shot(self):
        self.camera.StartGrabbing(1)
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_Mono8
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        image = converter.Convert(grabResult)
        img = image.GetArray()
        self.camera.StopGrabbing()
        return img

    def load_templates(self):
        self.cnt_template = np.load(self.template_path, allow_pickle=True)
        self.cnt_inner = np.load(self.inner_contour_path, allow_pickle=True)
        print(self.cnt_template.shape)
    
    @staticmethod
    def compute_iou(contour1, contour2, shape):
        mask1 = np.zeros(shape, dtype=np.uint8)
        mask2 = np.zeros(shape, dtype=np.uint8)
        cv2.drawContours(mask1, [contour1], -1, 255, thickness=cv2.FILLED)
        cv2.drawContours(mask2, [contour2], -1, 255, thickness=cv2.FILLED)
        intersection = np.logical_and(mask1, mask2).sum()
        union = np.logical_or(mask1, mask2).sum()
        return intersection / union if union != 0 else 0

    @staticmethod
    def rotate_contour(contour, angle, center):
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.transform(contour, rotation_matrix)
    
    def contour_detection(self, gray):
        try:
            start_time = time.time()
            _, image_edges = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
            contours_image, _ = cv2.findContours(image_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            min_perimeter = 100
            contours_image = [cnt for cnt in contours_image if cv2.arcLength(cnt, closed=True) > min_perimeter]
            
            cnt_image = None
            min_score = 1
            for contour in contours_image:
                score = cv2.matchShapes(self.cnt_template, contour, cv2.CONTOURS_MATCH_I1, 0)
                if score < min_score:
                    min_score = score
                    cnt_image = contour
            
            cnt_template = cv2.approxPolyDP(self.cnt_template, epsilon=1, closed=True)
            scale_factor = np.sqrt(cv2.contourArea(cnt_image) / cv2.contourArea(cnt_template))
            cnt_template_scaled = (cnt_template * scale_factor).astype(np.int32)
            self.cnt_inner = (self.cnt_inner * scale_factor).astype(np.int32)

            M_template, M_image = cv2.moments(cnt_template_scaled), cv2.moments(cnt_image)
            if M_template["m00"] != 0 and M_image["m00"] != 0:
                cx_template, cy_template = int(M_template["m10"] / M_template["m00"]), int(M_template["m01"] / M_template["m00"])
                cx_image, cy_image = int(M_image["m10"] / M_image["m00"]), int(M_image["m01"] / M_image["m00"])
                dx, dy = cx_image - cx_template, cy_image - cy_template
                cnt_template_scaled += (dx, dy)
                self.cnt_inner[:, :, 0:2] += (dx, dy)

            best_angle, best_iou, best_contour = self.optimize_rotation(cnt_template_scaled, cnt_image, gray.shape, cx_image, cy_image)
            end_time = time.time()
            processing_time = end_time - start_time
            
            return self.cnt_inner, cnt_image, best_contour, best_iou, best_iou, best_iou, processing_time
        except:
            pass

    def optimize_rotation(self, cnt_template_scaled, cnt_image, image_shape, cx_image, cy_image):
        best_angle, best_iou = 0, 0
        for angle in range(-180, 181, 30):
            rotated_contour = self.rotate_contour(cnt_template_scaled, angle, (cx_image, cy_image))
            iou = self.compute_iou(rotated_contour, cnt_image, image_shape[:2])
            if iou > best_iou:
                best_angle, best_iou = angle, iou
        return best_angle, best_iou, cnt_template_scaled

if __name__ == "__main__":
    matcher = ContourMatcher("/home/vinhdq/vision guide robot/temp_contour/selected_contour.npy",
                             "/home/vinhdq/vision guide robot/temp_contour/contour_inner.npy")
    image = matcher.capture_single_shot()
    cnt_inner, cnt_image, best_contour, best_iou, best_iou_translation, best_iou_size, processing_time = matcher.contour_detection(image)
    print(f"Best IoU: {best_iou}, Processing Time: {processing_time}s")

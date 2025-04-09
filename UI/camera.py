from pypylon import pylon
import cv2
import time
import numpy as np

class ContourDetector:
    def __init__(self, template_contour_path = None, inner_contour_path = None):
        self.template_contour_path = template_contour_path
        self.inner_contour_path = inner_contour_path

        self.camera = self.create_camera()

    def create_camera(self):
        TLFactory = pylon.TlFactory.GetInstance()
        devices = TLFactory.EnumerateDevices()
        if len(devices) == 0:
            raise Exception("No camera found")
        camera = pylon.InstantCamera(TLFactory.CreateDevice(devices[0]))
        camera.Open()
        # Configure camera
        camera.PixelFormat.SetValue("Mono8")  # Or "BayerRG8" for color camera
        camera.Width.SetValue(2440)
        camera.Height.SetValue(2048)
        return camera
    def rm_camera(self):
        print("a")
        self.camera.Close()
    def capture_single_shot(self):
        # Start capturing a single image
        self.camera.StartGrabbing(1)  # Capture only one image
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_Mono8
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        image = self.converter.Convert(grabResult)
        img = image.GetArray()
        self.camera.StopGrabbing()
        return img
    def grabbing(self):
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        image = self.converter.Convert(grabResult)
        img = image.GetArray()
        return img
    def compute_iou(self, contour1, contour2, shape):
        mask1 = np.zeros(shape, dtype=np.uint8)
        mask2 = np.zeros(shape, dtype=np.uint8)
        cv2.drawContours(mask1, [contour1], -1, 255, thickness=cv2.FILLED)
        cv2.drawContours(mask2, [contour2], -1, 255, thickness=cv2.FILLED)
        intersection = np.logical_and(mask1, mask2).sum()
        union = np.logical_or(mask1, mask2).sum()
        return intersection / union if union != 0 else 0

    def rotate_contour(self, contour, angle, center):
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.transform(contour, rotation_matrix)

    def grid_search(self, cnt_template_scaled, cnt_image, image_shape, cx_image, cy_image, step=30):
        best_angle, best_iou = 0, 0
        for angle in range(-180, 181, step):
            rotated_contour = self.rotate_contour(cnt_template_scaled, angle, (cx_image, cy_image))
            iou = self.compute_iou(rotated_contour, cnt_image, image_shape[:2])
            if iou > best_iou:
                best_angle, best_iou = angle, iou
        return best_angle, best_iou

    def golden_section_search(self, a, b, cnt_template_scaled, cnt_image, image_shape, cx_image, cy_image, tol=1):
        gr = (np.sqrt(5) - 1) / 2  # Golden ratio
        c = b - (b - a) * gr
        d = a + (b - a) * gr
        while abs(b - a) > tol:
            cnt_c = self.rotate_contour(cnt_template_scaled, c, (cx_image, cy_image))
            iou_c = self.compute_iou(cnt_c, cnt_image, image_shape[:2])
            cnt_d = self.rotate_contour(cnt_template_scaled, d, (cx_image, cy_image))
            iou_d = self.compute_iou(cnt_d, cnt_image, image_shape[:2])
            if iou_c > iou_d:
                b = d
            else:
                a = c
            c = b - (b - a) * gr
            d = a + (b - a) * gr
        best_angle = (a + b) / 2
        best_angle_inv = best_angle + 180
        best_contour = self.rotate_contour(cnt_template_scaled, best_angle, (cx_image, cy_image))
        best_contour_inv = self.rotate_contour(cnt_template_scaled, best_angle_inv, (cx_image, cy_image))
        best_iou = self.compute_iou(best_contour, cnt_image, image_shape[:2])
        best_iou_inv = self.compute_iou(best_contour_inv, cnt_image, image_shape[:2])
        if best_iou_inv > best_iou:
            print("inv",best_iou_inv)
            print("bes",best_iou)
            return best_angle_inv,best_iou_inv,best_contour_inv
        return best_angle, best_iou, best_contour

    def contour_detection(self, gray,thr = 100):
        _, image_edges = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)
        contours_image, _ = cv2.findContours(image_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        start_time = time.time()

        # Debugging: Print the number of contours detected
        print(f"Number of contours detected: {len(contours_image)}")

        # Load contours from .npy files
        cnt_template = np.load(self.template_contour_path, allow_pickle=True)
        cnt_inner = np.load(self.inner_contour_path, allow_pickle=True)

        # Filter contours based on perimeter
        min_perimeter = 100  # Minimum perimeter threshold
        contours_image = [cnt for cnt in contours_image if cv2.arcLength(cnt, closed=True) > min_perimeter]
        print(f"Number of contours after filtering: {len(contours_image)}")

        # Check if any contours are left after filtering
        if not contours_image:
            raise ValueError("No contours detected after filtering.")

        # Find the best matching contour
        cnt_image = None
        min_score = float('inf')  # Initialize with a large value
        for contour in contours_image:
            score = cv2.matchShapes(cnt_template, contour, cv2.CONTOURS_MATCH_I1, 0)
            if score < min_score:
                min_score = score
                cnt_image = contour

        # Check if a valid contour was found
        if cnt_image is None:
            raise ValueError("No matching contour found.")

        print(f"Best matching contour score: {min_score}")

        # Smooth the template contour
        cnt_template = cv2.approxPolyDP(cnt_template, epsilon=1, closed=True)

        # Calculate scale factor based on area
        area_template = cv2.contourArea(cnt_template)
        area_image = cv2.contourArea(cnt_image)
        scale_factor = np.sqrt(area_image / area_template)

        # Scale the template and inner contours
        cnt_template_scaled = (cnt_template * scale_factor).astype(np.int32)
        cnt_inner = (cnt_inner * scale_factor).astype(np.int32)

        # Find the centers of the contours
        M_template = cv2.moments(cnt_template_scaled)
        M_image = cv2.moments(cnt_image)
        if M_template["m00"] != 0 and M_image["m00"] != 0:
            cx_template = int(M_template["m10"] / M_template["m00"])
            cy_template = int(M_template["m01"] / M_template["m00"])
            cx_image = int(M_image["m10"] / M_image["m00"])
            cy_image = int(M_image["m01"] / M_image["m00"])
            # Translate the template contour to match the image contour
            dx = cx_image - cx_template
            dy = cy_image - cy_template
            cnt_template_scaled += (dx, dy)
            cnt_inner[:, :, 0:2] += (dx, dy)

        # Step 1: Perform grid search for initial rotation
        best_grid_angle, _ = self.grid_search(cnt_template_scaled, cnt_image, gray.shape, cx_image, cy_image)

        # Step 2: Refine rotation using golden-section search
        search_range = 30  # Search range around the best grid angle
        best_angle, best_iou, best_contour = self.golden_section_search(
            best_grid_angle - search_range, best_grid_angle + search_range,
            cnt_template_scaled, cnt_image, gray.shape, cx_image, cy_image
        )

        # Rotate the inner contour
        cnt_inner[:, :, 0:2] = self.rotate_contour(cnt_inner[:, :, 0:2], best_angle, (cx_image, cy_image))

        # Optimize translation
        best_iou_translation = best_iou
        for dx in [-5, 0, 5]:
            for dy in [-5, 0, 5]:
                shifted_contour = best_contour + (dx, dy)
                iou = self.compute_iou(shifted_contour, cnt_image, gray.shape[:2])
                if iou > best_iou_translation:
                    best_iou_translation = iou
                    best_contour = shifted_contour

        # Optimize scaling
        best_iou_size = best_iou_translation
        for scale in [0.95, 1.05]:
            resized_contour = (best_contour * scale).astype(np.int32)
            iou = self.compute_iou(resized_contour, cnt_image, gray.shape[:2])
            if iou > best_iou_size:
                best_iou_size = iou
                best_contour = resized_contour

        end_time = time.time()
        processing_time = end_time - start_time

        return cnt_inner, cnt_image, best_contour, best_iou, best_iou_translation, best_iou_size, processing_time
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
from create_template_contour_threshol import ContourEditor
from pypylon import pylon
import camera

# Hàm tính IoU
def compute_iou(contour1, contour2, shape):
    mask1 = np.zeros(shape, dtype=np.uint8)
    mask2 = np.zeros(shape, dtype=np.uint8)
    cv2.drawContours(mask1, [contour1], -1, 255, thickness=cv2.FILLED)
    cv2.drawContours(mask2, [contour2], -1, 255, thickness=cv2.FILLED)
    intersection = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    return intersection / union if union != 0 else 0
# Tìm góc xoay tối ưu bằng Golden-section search
def rotate_contour(contour, angle, center):
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.transform(contour, rotation_matrix)
def grid_search(cnt_template_scaled, cnt_image, image_shape, cx_image, cy_image, step=30):
    best_angle, best_iou = 0, 0
    for angle in range(-180, 181, step):
        rotated_contour = rotate_contour(cnt_template_scaled, angle, (cx_image, cy_image))
        iou = compute_iou(rotated_contour, cnt_image, image_shape[:2])
        if iou > best_iou:
            best_angle, best_iou = angle, iou
    return best_angle, best_iou
def golden_section_search(a, b, cnt_template_scaled, cnt_image, image_shape, cx_image, cy_image, tol=1):
    gr = (np.sqrt(5) - 1) / 2  # Golden ratio
    c = b - (b - a) * gr
    d = a + (b - a) * gr
    while abs(b - a) > tol:
        cnt_c = rotate_contour(cnt_template_scaled, c, (cx_image, cy_image))
        iou_c = compute_iou(cnt_c, cnt_image, image_shape[:2])
        cnt_d = rotate_contour(cnt_template_scaled, d, (cx_image, cy_image))
        iou_d = compute_iou(cnt_d, cnt_image, image_shape[:2])
        if iou_c > iou_d:
            b = d
        else:
            a = c
        c = b - (b - a) * gr
        d = a + (b - a) * gr
    best_angle = (a + b) / 2
    best_contour = rotate_contour(cnt_template_scaled, best_angle, (cx_image, cy_image))
    best_iou = compute_iou(best_contour, cnt_image, image_shape[:2])
    return best_angle, best_iou, best_contour
def contourDetection(gray):
    _,image_edges = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
    contours_image, _ = cv2.findContours(image_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    start_time = time.time()
    # Load contour từ file .npy
    cnt_template = np.load('/home/vinhdq/I&C_PROJECT/temp_contour/selected_contour.npy', allow_pickle=True)
    cnt_inner = np.load('/home/vinhdq/I&C_PROJECT/temp_contour/contour_inner.npy', allow_pickle=True)
    start_time = time.time()

    # Lọc contour dựa trên chu vi
    min_perimeter = 100  # Ngưỡng chu vi tối thiểu
    contours_image = [cnt for cnt in contours_image if cv2.arcLength(cnt, closed=True) > min_perimeter]
    print(f'Số lượng contours sau khi lọc trong ảnh thực tế: {len(contours_image)}')
    # fit process
    cnt_image = None
    min_score = 1
    for contour in contours_image:
        score = cv2.matchShapes(cnt_template, contour, cv2.CONTOURS_MATCH_I1, 0)
        if score < min_score:
            min_score = score
            cnt_image = contour
    print(f"Contour giống nhất có score: {min_score}")
    # Làm mượt contour template
    cnt_template = cv2.approxPolyDP(cnt_template, epsilon=1, closed=True)
    # Tính diện tích của hai contour
    area_template = cv2.contourArea(cnt_template)
    area_image = cv2.contourArea(cnt_image)
    # Tính tỉ lệ scale dựa trên diện tích
    scale_factor = np.sqrt(area_image / area_template)
    # Resize contour template theo tỉ lệ
    cnt_template_scaled = cnt_template * scale_factor
    cnt_template_scaled = cnt_template_scaled.astype(np.int32)
    cnt_inner = (cnt_inner * scale_factor).astype(np.int32)
    # Tìm tâm của hai contour
    M_template = cv2.moments(cnt_template_scaled)
    M_image = cv2.moments(cnt_image)
    if M_template["m00"] != 0 and M_image["m00"] != 0:
        cx_template = int(M_template["m10"] / M_template["m00"])
        cy_template = int(M_template["m01"] / M_template["m00"])
        cx_image = int(M_image["m10"] / M_image["m00"])
        cy_image = int(M_image["m01"] / M_image["m00"])
        # Tính toán vector dịch chuyển
        dx = cx_image - cx_template
        dy = cy_image - cy_template
        # Dịch chuyển contour template về vị trí của contour ảnh thực tế
        cnt_template_scaled += (dx, dy) 
        cnt_inner[:,:,0:2] += (dx, dy) 
    # Step 1: Grid Search sơ bộ
    best_grid_angle, _ = grid_search(cnt_template_scaled, cnt_image, gray.shape, cx_image, cy_image)
    # Áp dụng Golden-section search để tìm góc tốt nhất
    search_range = 30  # Giảm phạm vi tìm kiếm quanh góc tốt nhất
    best_angle, best_iou, best_contour = golden_section_search(
        best_grid_angle - search_range, best_grid_angle + search_range,
        cnt_template_scaled, cnt_image, gray.shape, cx_image, cy_image
    )
    # best_angle, best_iou_rotation, best_contour = golden_section_search(0, 180, cnt_template_scaled, cnt_image, image, cx_image, cy_image, tol=1)
    # cnt_inner[:,:,0:2] = cv2.transform(cnt_inner[:,:,0:2],cv2.getRotationMatrix2D((cx_image, cy_image), best_angle, 1.0))
    cnt_inner[:, :, 0:2] = rotate_contour(cnt_inner[:, :, 0:2], best_angle, (cx_image, cy_image))
    # Dịch chuyển template xung quanh tâm để tối ưu IoU
    best_iou_translation = best_iou
    for dx in [-5, 0, 5]:
        for dy in [-5, 0, 5]:
            shifted_contour = best_contour + (dx, dy)
            iou = compute_iou(shifted_contour, cnt_image, gray.shape[:2])
            if iou > best_iou_translation:
                best_iou_translation = iou
                best_contour = shifted_contour
    # Resize lên rồi xuống để tối ưu IoU
    best_iou_size = best_iou_translation
    for scale in [0.95, 1.05]:
        resized_contour = (best_contour * scale).astype(np.int32)
        iou = compute_iou(resized_contour, cnt_image, gray.shape[:2])
        if iou > best_iou_size:
            best_iou_size = iou
            best_contour = resized_contour
    end_time = time.time()
    processing_time = end_time - start_time
    return cnt_inner,cnt_image,best_contour,best_iou,best_iou_translation,best_iou_size,processing_time
# Đọc ảnh thực tế từ camera hoặc file
cam = camera.create_camera()
while(1):
    gray = camera.capture_single_shot(cam)
    cnt_inner,cnt_image,best_contour,best_iou,best_iou_translation,best_iou_size,processing_time = contourDetection(gray)
    # Vẽ kết quả lên ảnh gốc
    cv2.drawContours(gray, [cnt_inner[:,:,0:2]], -1, (0, 255, 0), 2)
    cv2.drawContours(gray, [cnt_image], -1, (0, 255, 0), 2)
    cv2.drawContours(gray, [best_contour], -1, (255, 0, 0), 2)
    cv2.putText(gray, f'IoU Rotation: {best_iou:.4f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(gray, f'IoU Translation: {best_iou_translation:.4f}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(gray, f'IoU Size: {best_iou_size:.4f}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(gray, f'latency: {processing_time:.4f}', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    # Hiển thị kết quả
    plt.figure(figsize=(50, 25))
    plt.imshow(cv2.cvtColor(gray, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.title('Shape Matching Result')
    plt.show()
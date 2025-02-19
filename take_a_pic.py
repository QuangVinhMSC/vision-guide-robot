from pypylon import pylon
import cv2
import numpy as np

# Tạo đối tượng factory để lấy danh sách camera
factory = pylon.TlFactory.GetInstance()
devices = factory.EnumerateDevices()

if len(devices) == 0:
    raise RuntimeError("Không tìm thấy camera nào!")

# Khởi tạo camera
camera = pylon.InstantCamera(factory.CreateDevice(devices[0]))
camera.Open()

# Chụp một ảnh duy nhất
camera.StartGrabbingMax(1)
grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

if grabResult.GrabSucceeded():
    # Chuyển dữ liệu từ camera sang mảng numpy
    image = grabResult.Array
    
    # Lưu ảnh
    filename = "/home/vinhdq/I&C_PROJECT/image/captured_image.png"
    cv2.imwrite(filename, image)
    print(f"Ảnh đã được lưu thành công: {filename}")
else:
    print("Lỗi khi chụp ảnh")

# Giải phóng tài nguyên
grabResult.Release()
camera.Close()

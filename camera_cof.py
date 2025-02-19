from pypylon import pylon
import cv2
import numpy as np

# Kết nối với camera
TLFactory = pylon.TlFactory.GetInstance()
devices = TLFactory.EnumerateDevices()
if len(devices) == 0:
    raise Exception("No camera found")

camera = pylon.InstantCamera(TLFactory.CreateDevice(devices[0]))
camera.Open()

# Cấu hình camera
camera.PixelFormat.SetValue("Mono8")  # Hoặc "BayerRG8" nếu là camera màu
camera.Width.SetValue(2440)
camera.Height.SetValue(2048)

# Bắt đầu lấy ảnh
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_Mono8
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

while camera.IsGrabbing():
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    if grabResult.GrabSucceeded():
        image = converter.Convert(grabResult)
        img = image.GetArray()
        
        # Hiển thị ảnh
        cv2.namedWindow('Camera acA2440-20gm', cv2.WINDOW_NORMAL)  # Cho phép điều chỉnh kích thước cửa sổ
        cv2.resizeWindow('Camera acA2440-20gm', 1500, 1000)  # Đặt kích thước cửa sổ cụ thể
        cv2.imshow('Camera acA2440-20gm', img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    grabResult.Release()

# Giải phóng tài nguyên
camera.StopGrabbing()
camera.Close()
cv2.destroyAllWindows()
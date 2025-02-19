from pypylon import pylon
import cv2
import numpy as np

def create_camera():
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
    return camera
def capture_single_shot(camera):
    # Bắt đầu lấy ảnh
    camera.StartGrabbing(1)  # Chỉ lấy một ảnh duy nhất
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_Mono8
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    image = converter.Convert(grabResult)
    img = image.GetArray()
    camera.StopGrabbing()
    return img

# Gọi hàm để chụp ảnh
if __name__ == "__main__":
    camera = create_camera()
    img = capture_single_shot(camera)
    cv2.imshow('Single Shot', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    camera.Close()
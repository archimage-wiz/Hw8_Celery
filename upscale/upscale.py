import cv2
import numpy as np
from cv2 import dnn_superres


def upscale_old(image_data, output_path: str, model_path: str = 'upscale/EDSR_x2.pb') -> None:
    scaler = dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)
    # image = cv2.imread(image)

    np_arr = np.frombuffer(image_data, np.uint8)
    img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    result = scaler.upsample(img_np)
    cv2.imwrite(output_path, result)

# def example():
#     upscale('ava1.jpg', 'ava2.jpg')
#
#
# if __name__ == '__main__':
#     example()

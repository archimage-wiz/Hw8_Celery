import os

import cv2
import gridfs
import nanoid
import numpy as np
import pymongo
from celery import Celery
from cv2 import dnn_superres
from dotenv import load_dotenv

load_dotenv()

CELERY_BROKER = os.getenv("CELERY_BROKER")
PG_DSN = os.getenv("PG_DSN")
MONGO_DSN = os.getenv("MONGO_DSN")

print(PG_DSN)
print(CELERY_BROKER)

celery_app = Celery("upscale_app", backend=f"db+{PG_DSN}", broker=CELERY_BROKER)

client = pymongo.MongoClient(MONGO_DSN, connect=False)
db = client['app_files_v1']


@celery_app.task(bind=True)
def upscale(self, image_data, model_path: str = 'upscale/EDSR_x2.pb') -> None:
    scaler = dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)
    np_arr = np.frombuffer(image_data, np.uint8)
    img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    result = scaler.upsample(img_np)
    _, image = cv2.imencode(".jpg", result)
    image_bytes = image.tobytes()
    fs = gridfs.GridFS(db, f"images")
    result = fs.put(image_bytes,
                    filename=f"{nanoid.generate()}.jpg",
                    task_id=self.request.id)

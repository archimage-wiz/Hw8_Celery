import io
import os

import gridfs
import pymongo
from celery.result import AsyncResult
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask.views import MethodView

from upscale.tasks import celery_app, upscale

load_dotenv()

MONGO_DSN = os.getenv("MONGO_DSN")

flask_app = Flask("upscale_app")
client = pymongo.MongoClient(MONGO_DSN, connect=False)
db = client['app_files_v1']


class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


celery_app.Task = ContextTask


class UpscaleApp(MethodView):
    def get(self):
        if task_id := request.args.get('task_id'):
            res = AsyncResult(task_id, app=celery_app)
            if res.ready():
                fs = gridfs.GridFS(db, f"images")
                fs_res = fs.find_one({"task_id": task_id})
                file_bytes = fs_res.read()
                file = io.BytesIO(file_bytes)
                file.seek(0)
                return send_file(file, mimetype="image/jpeg", download_name=fs_res.filename)
            else:
                return jsonify({"Status": "Not ready"})

        return jsonify(
            {
                "Status": "error",
                "Details": "provide task_id"
            }
        )

    def post(self):
        image_obj = request.files.get("image")
        # result = str(mongo.save_file(f"{nanoid.generate()}{image_obj.filename}", image_obj))

        # fs = gridfs.GridFS(db, f"images")
        # result = fs.put(image_obj, filename=f"{nanoid.generate()}-{image_obj.filename}", anydata="yes")
        res = upscale.delay(image_obj.stream.read())

        return jsonify(
            {
                "status": "ok",
                "task_id": res.id
            }
        )


flask_app.add_url_rule("/demo/upscale/", methods=["POST"], view_func=UpscaleApp.as_view("upscale_app"))
flask_app.add_url_rule("/demo/upscale/", methods=["GET"], view_func=UpscaleApp.as_view("sdsd"))

if __name__ == "__main__":
    print("app run")
    flask_app.run(host="127.0.0.1", port=5000)

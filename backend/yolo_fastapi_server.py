from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import io
from PIL import Image
import numpy as np
import cv2
from ultralytics import YOLO
from fastapi.responses import JSONResponse
import logging
from io import BytesIO
import base64

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Class mapping từ mô hình bạn vừa train (gồm 9 lớp)
class_mapping = {
    '0': 'chai_nuoc',
    '1': 'nap_chai',
    '2': 'que_de_luoi',
    '3': 'que_xien',
    '4': 'bong_bay',
    '5': 'nit',
    '6': 'giay_mau',
    '7': 'ong_hut',
    '8': 'bia_cat_tong'
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model
try:
    model = YOLO('best.pt')
except Exception as e:
    logging.error(f"Could not load model: {e}")
    raise RuntimeError("Model load failed")

def pil_to_cv2(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

def cv2_to_pil(image: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

def encode_image_to_base64(image: Image.Image) -> str:
    if image.mode == "RGBA":
        image = image.convert("RGB")
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def convert_numpy_types(obj: Any):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    return obj

@app.post("/det")
async def detection(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        image = Image.open(BytesIO(image_data))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Cannot read image")

    results = model(source=image, conf=0.3, iou=0.5)

    img_cv2 = pil_to_cv2(image)
    class_counts = {}
    det = [0] * len(class_mapping)

    for result in results:
        boxes = result.boxes.cpu().numpy()
        xyxy = boxes.xyxy
        cls_ids = boxes.cls.astype(int)

        for box, cls_id in zip(xyxy, cls_ids):
            cv2.rectangle(img_cv2, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)
            class_name = class_mapping.get(str(cls_id), f"Unknown({cls_id})")
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            det[cls_id] += 1

    img_result = cv2_to_pil(img_cv2)
    base64_original = encode_image_to_base64(image)
    base64_result = encode_image_to_base64(img_result)

    return {
        "data": {
            "base64_r": base64_result,
            "class_mapping": class_mapping,
            "result": {
                "dict": class_counts,
                "det": det,
            },
        },
        "msg": "success",
        "code": 200
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import io
from PIL import Image
import numpy as np
import cv2
from fastapi.responses import JSONResponse
import logging
from io import BytesIO
import base64

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Class mapping for common objects (simplified for demonstration)
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Simple object detection using OpenCV contours (placeholder for your custom model)
def detect_objects(image_cv2):
    # Convert to grayscale for processing
    gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get binary image
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detections = []
    for contour in contours:
        # Filter small contours
        if cv2.contourArea(contour) > 500:
            x, y, w, h = cv2.boundingRect(contour)
            detections.append({
                'bbox': [x, y, x+w, y+h],
                'class_id': 0,  # Default to first class
                'confidence': 0.8
            })
    
    return detections

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

    img_cv2 = pil_to_cv2(image)
    class_counts = {}
    det = [0] * len(class_mapping)

    # Use simple detection instead of YOLO
    detections = detect_objects(img_cv2)

    for detection in detections:
        bbox = detection['bbox']
        cls_id = detection['class_id']
        
        # Draw bounding box
        cv2.rectangle(img_cv2, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
        
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

@app.get("/")
async def root():
    return {"message": "Object Detection API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

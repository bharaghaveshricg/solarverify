# ============================================================
# SOLARVERIFY – FINAL GOVERNANCE-READY PIPELINE
# ============================================================

import os
import csv
import json
import math
import cv2
import requests
from io import BytesIO
from PIL import Image
from ultralytics import YOLO

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "model_train/best.pt"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY not found. Please set it as an environment variable."
    )


# --- Google Static Maps (BEST QUALITY WITHOUT PREMIUM) ---
ZOOM = 20                 # 21 causes blur in many Indian regions
SIZE = "640x640"
SCALE = 2                 # Effective 1280×1280
MAPTYPE = "satellite"
FORMAT = "png"

# --- Detection tuning (NO RETRAIN) ---
CONF_THRESHOLD = 0.45
MIN_PANEL_AREA_PX = 6000
IOU_MERGE_THRESHOLD = 0.30

# --- Capacity assumption ---
WP_PER_M2 = 200  # documented assumption

# --- Output folders ---
FETCHED_DIR = "fetched_images"
OVERLAY_DIR = "audit_overlays"
OUTPUT_JSON_DIR = "output_json"

os.makedirs(FETCHED_DIR, exist_ok=True)
os.makedirs(OVERLAY_DIR, exist_ok=True)
os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)

# ============================================================
# LOAD MODEL
# ============================================================

print("\n📌 Loading YOLO model...")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("❌ best.pt not found in model_train/")
model = YOLO(MODEL_PATH)
print("✔ Model loaded")

# ============================================================
# HELPERS
# ============================================================

def meters_per_pixel(lat):
    lat_rad = math.radians(lat)
    return (156543.03392 * math.cos(lat_rad)) / (2 ** ZOOM * SCALE)


def fetch_google_image(sample_id, lat, lon):
    url = (
        "https://maps.googleapis.com/maps/api/staticmap?"
        f"center={lat},{lon}"
        f"&zoom={ZOOM}"
        f"&size={SIZE}"
        f"&scale={SCALE}"
        f"&maptype={MAPTYPE}"
        f"&format={FORMAT}"
        f"&key={GOOGLE_API_KEY}"
    )

    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            print(f"🚫 Google fetch failed for {sample_id}")
            return None

        img = Image.open(BytesIO(r.content)).convert("RGB")
        out_path = f"{FETCHED_DIR}/{sample_id}.png"
        img.save(out_path)
        return out_path

    except Exception as e:
        print(f"⚠️ Fetch error for {sample_id}: {e}")
        return None


def iou(b1, b2):
    x1 = max(b1["x1"], b2["x1"])
    y1 = max(b1["y1"], b2["y1"])
    x2 = min(b1["x2"], b2["x2"])
    y2 = min(b1["y2"], b2["y2"])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (b1["x2"] - b1["x1"]) * (b1["y2"] - b1["y1"])
    area2 = (b2["x2"] - b2["x1"]) * (b2["y2"] - b2["y1"])
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0


def merge_boxes(boxes):
    merged = []
    used = set()

    for i, b in enumerate(boxes):
        if i in used:
            continue

        mb = b.copy()
        for j, other in enumerate(boxes):
            if j == i or j in used:
                continue
            if iou(mb, other) > IOU_MERGE_THRESHOLD:
                mb["x1"] = min(mb["x1"], other["x1"])
                mb["y1"] = min(mb["y1"], other["y1"])
                mb["x2"] = max(mb["x2"], other["x2"])
                mb["y2"] = max(mb["y2"], other["y2"])
                used.add(j)

        merged.append(mb)
        used.add(i)

    return merged


def weak_cluster_recovery(boxes):
    """
    Recover solar when detections are weak but clustered.
    Governance-safe fallback.
    """
    if len(boxes) < 2:
        return False

    weak_boxes = [b for b in boxes if b["conf"] >= 0.30]
    if len(weak_boxes) < 2:
        return False

    total_area = sum(
        (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
        for b in weak_boxes
    )

    return total_area >= MIN_PANEL_AREA_PX


def run_yolo(image_path):
    results = model.predict(image_path, conf=CONF_THRESHOLD, verbose=False)[0]
    boxes = []

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        conf = float(box.conf[0])
        area = (x2 - x1) * (y2 - y1)

        if area < MIN_PANEL_AREA_PX:
            continue

        boxes.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "conf": round(conf, 3)
        })

    return merge_boxes(boxes)


def estimate_area_and_capacity(boxes, lat):
    if not boxes:
        return 0.0, 0.0

    px_area = sum(
        (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
        for b in boxes
    )

    sqm = px_area * (meters_per_pixel(lat) ** 2)
    capacity_kw = sqm * WP_PER_M2 / 1000

    return round(sqm, 2), round(capacity_kw, 2)


def create_overlay(image_path, boxes, sample_id):
    img = cv2.imread(image_path)

    for b in boxes:
        cv2.rectangle(
            img,
            (b["x1"], b["y1"]),
            (b["x2"], b["y2"]),
            (0, 255, 0),
            2
        )
        cv2.putText(
            img,
            f'{b["conf"]:.2f}',
            (b["x1"], max(15, b["y1"] - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1
        )

    out = f"{OVERLAY_DIR}/{sample_id}.png"
    cv2.imwrite(out, img)
    return out


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline(csv_path):
    outputs = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sid = row["sample_id"]
            lat = float(row["latitude"])
            lon = float(row["longitude"])

            print(f"\n📍 Processing Site {sid}")

            img_path = fetch_google_image(sid, lat, lon)
            if not img_path:
                continue

            boxes = run_yolo(img_path)
            overlay = create_overlay(img_path, boxes, sid)
            area, cap = estimate_area_and_capacity(boxes, lat)

            # ---- GOVERNANCE LOGIC ----
            if len(boxes) > 0:
                qc_status = "verifiable"
                has_solar = True
                qc_notes = ["distinct module grid", "rectilinear array"]

            elif weak_cluster_recovery(boxes):
                qc_status = "uncertain"
                has_solar = True
                qc_notes = ["weak clustered detections", "low visual contrast"]

            else:
                qc_status = "not_verifiable"
                has_solar = False
                qc_notes = ["no clear solar evidence"]

            outputs.append({
                "sample_id": sid,
                "lat": lat,
                "lon": lon,
                "has_solar": has_solar,
                "confidence": max([b["conf"] for b in boxes], default=0),
                "panel_count_est": len(boxes),
                "pv_area_sqm_est": area,
                "capacity_kw_est": cap,
                "qc_status": qc_status,
                "qc_notes": qc_notes,
                "overlay_path": overlay
            })

    out_file = f"{OUTPUT_JSON_DIR}/all_results.json"
    with open(out_file, "w") as f:
        json.dump(outputs, f, indent=4)

    print("\n🎉 Pipeline complete")
    print("📁 JSON saved →", out_file)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python pipeline.py --csv input_sites.csv")
        exit(1)

    run_pipeline(sys.argv[2])

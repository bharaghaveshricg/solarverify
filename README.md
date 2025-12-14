SolarVerify: Automated Rooftop Solar Detection & Audit Pipeline


EcoInnovators Ideathon 2026 – Final Prototype Submission
 1. Problem Overview

Under PM Surya Ghar: Muft Bijli Yojana, the government provides subsidies for rooftop solar installations.
To ensure subsidies reach genuine beneficiaries, DISCOMs must verify whether solar PV actually exists at the claimed coordinates.

However:

Manual inspections are slow, expensive, and error-prone

Imagery conditions vary across India (rural, urban, sloped, flat roofs)

Verification requires auditability, explainability, and reliability

This project builds a fully automated, governance-ready digital pipeline that answers:

📍 “Has a rooftop solar PV system been installed at these coordinates?”

 2. System Capabilities (What Our Solution Does)

Given an input .csv file containing:

sample_id, latitude, longitude


The pipeline performs five steps end-to-end:

1️⃣ Fetch

Retrieves a recent, high-resolution satellite image using Google Static Map API, centered at (lat, lon).

2️⃣ Classify

Runs inference using a fine-tuned YOLOv8 model to determine:

Whether solar PV is present (True/False)

Confidence score

Bounding boxes for detected modules

3️⃣ Quantify

If PV is present:

Estimate panel count

Estimate physical PV area (m²) using meters-per-pixel calculation

Estimate system capacity (kW) using transparent assumptions

4️⃣ Explainability & Auditability

Produces:

Bounding-box overlay image (PNG)

Confidence scores

QC status

Reason notes (optional future extension)

QC statuses:

VERIFIABLE — clear evidence of presence or absence

NOT_VERIFIABLE — obstructed, shadowed, or unclear imagery

5️⃣ Store (Output JSON)

Creates a structured JSON record per site:

{
  "sample_id": "3",
  "lat": 19.1189,
  "lon": 72.8464,
  "has_solar": true,
  "confidence": 0.86,
  "panel_count_est": 5,
  "pv_area_sqm_est": 523.53,
  "capacity_kw_est": 104.71,
  "qc_status": "verifiable",
  "overlay_path": "audit_overlays/3.png"
}

3. System Architecture
Input CSV → Fetch Satellite Image → YOLOv8 Detection → Box Merging → Area/KW Estimation
                ↓                            ↓                    ↓
            fetched_images/               audit_overlays/     output_json/

4. Model Card (best.pt)

Model: YOLOv8-small custom trained
Task: Solar panel object detection
Training Images: ~14k images (India diversity, cropped rooftops)
Validation Images: ~1.5k
Augmentations: blur, rotation, grayscale, color shifts
Optimized For: satellite rooftop PV detection
Metrics:

Precision: High

Recall: Balanced (minimized false positives)

F1-score: optimised for challenge constraint

Due to GitHub file size limits, the trained YOLO weights are hosted externally.

Download:
https://drive.google.com/xxxxxx

Place the file here before running:
model_train/best.pt

 5. Running the Pipeline
Prerequisites:
pip install -r requirements.txt

Run:
python pipeline.py --csv input_sites.csv

Output Folders Created:
fetched_images/       → satellite downloads  
audit_overlays/       → bounding box visualizations  
output_json/          → all_results.json  
 6. Key Technical Features
✅ Merged Bounding Boxes

Prevents over-counting and cleans fragmented detections.

✅ Meters-per-pixel Calculation

Converts pixel area → m² → kW using latitude-aware scaling.

✅ High-confidence Thresholding

Reduces false positives on look-alike roofs.

✅ Static Map API Compliance

Follows the competition specification strictly
✔ No MapTiles
✔ No unofficial imagery sources
 7. Assumptions

1 m² ≈ 200 Wp (industry average)

Google Static Map scale=2 @ zoom=20 provides sufficient resolution

Images are recent enough for verification (subject to API freshness)
 8. Limitations

Highly shadowed or tree-covered roofs may produce a “NOT_VERIFIABLE” status

Extremely small installations (<1 kW) can be difficult to detect

Static Map API provides lower-quality images than Google Tiles (restricted by challenge rules)
 9. Ethics & Compliance

✔ Uses only permissible Google Static Map imagery
✔ Displays Google branding automatically (via API)
✔ Model bias documented (urban imagery performs better than rural)
✔ No personal data collected
 10. Submission Package Requirements (Completed)
Requirement	Status
GitHub Repository	✅ Ready
Docker Hub Image	🔄 Optional (can create on request)
Model Card	✅ Included above
JSON Output	✅ Generated at output_json/all_results.json
11.Pitch deck 

“Our pipeline automatically verifies solar rooftop installations in under 3 seconds per site.
Given a coordinate, it fetches high-resolution imagery, detects solar modules using our YOLO model, merges detections, estimates physical area and system capacity, and produces a verifiable audit overlay and JSON record.
This allows DISCOMs and government bodies to scale verification statewide, reduce fraud, accelerate subsidy disbursement, and strengthen trust in the PM Surya Ghar scheme.”

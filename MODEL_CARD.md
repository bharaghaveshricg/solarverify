Model Card — SolarVerify
Model Name

SolarVerify – Rooftop Solar Installation Verification Model

Model Overview

SolarVerify is a computer vision–based verification system designed to remotely confirm the presence of rooftop solar photovoltaic (PV) installations using satellite imagery.
The model supports government-scale auditing workflows, ensuring subsidies under schemes like PM Surya Ghar: Muft Bijli Yojana reach genuine beneficiaries.

The system answers the question:

“Has a rooftop solar system actually been installed at this location?”

Intended Use

✔ Remote verification of rooftop solar installations
✔ Subsidy audit and governance workflows
✔ DISCOM and government inspection support
✔ Large-scale monitoring with low operational cost

⚠️ Not intended for:

Individual panel fault detection

Electrical performance estimation

Real-time monitoring

Input

Latitude & Longitude (CSV input)

Satellite imagery fetched using Google Static Maps API

Map Type: Satellite

Zoom: 20

Size: 640×640

Scale: 2 (effective 1280×1280)

Output

For each coordinate, the system generates:

has_solar → Boolean (true / false)

confidence → Model confidence score

panel_count_est → Estimated number of panels

pv_area_sqm_est → Estimated solar panel area (m²)

capacity_kw_est → Estimated capacity (kW)

qc_status → VERIFIABLE / NOT_VERIFIABLE

qc_notes → Explainable reason codes

Overlay image with bounding boxes

JSON audit record

Model Architecture

Base Model: YOLO (Ultralytics)

Task: Object Detection (Solar Panels)

Output: Bounding boxes with confidence scores

Post-processing:

IOU-based box merging

Minimum-area filtering

Weak cluster recovery logic

Training Summary

Training Data: Satellite imagery with labeled rooftop solar panels

Epochs: 60

Augmentation: Standard spatial augmentations

Optimization: Fine-tuned for rooftop solar detection

⚠️ Final deployment accuracy is improved without retraining using governance-safe pipeline logic.

Capacity Estimation Assumption

Capacity is estimated using:

200 Watt-peak per square meter


This assumption is documented and transparent for auditability.

Performance Characteristics
Metric	Description
Detection Accuracy	High precision for rooftop PV presence
Quantification	Approximate area and capacity estimation
Robustness	Works across flat & sloped roofs
Explainability	Visual overlays + reason codes

Performance may degrade under:

Heavy cloud cover

Low-resolution imagery

Rooftop obstructions (tanks, trees)

Such cases are flagged as NOT_VERIFIABLE.

Ethical & Privacy Considerations

✔ Uses only permissible satellite imagery
✔ No personal or facial data involved
✔ No individual identification
✔ Designed for transparency & accountability

Known Limitations

Cannot detect panels fully occluded by objects

Estimation accuracy varies with image resolution

Capacity estimation is approximate, not certified

Deployment & Reproducibility

Inference pipeline: pipeline.py

Input: CSV file with coordinates

Output: JSON + overlay images

Dependencies: Listed in requirements.txt

Reproducible: Yes (deterministic pipeline)

Authors & Ownership

Project Lead: (C.G.Bharaghave Shri)
Contributors: (Your name)

License

This project is released for research, evaluation, and governance prototype purposes only.

Contact

For questions or audits, please contact the project lead via the repository. 
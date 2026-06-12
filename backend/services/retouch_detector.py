"""Layer 4: Auxiliary Retouch Detector — Weak ELA & Post-Processing Flags."""
from io import BytesIO
from PIL import Image
import numpy as np
import cv2

def analyze(image_bytes: bytes) -> list:
    """Detect minor tampering and retouching using Error Level Analysis (ELA).
    Note: In Truth Engine Lite, ELA is considered WEAK auxiliary evidence.
    """
    try:
        # Save as highly compressed JPEG in memory
        img = Image.open(BytesIO(image_bytes)).convert('RGB')
        buffer = BytesIO()
        img.save(buffer, 'JPEG', quality=90)
        img_compressed = Image.open(buffer)
        
        arr_orig = np.array(img).astype(np.float32)
        arr_comp = np.array(img_compressed).astype(np.float32)
    except Exception:
        return _fallback()

    # Calculate ELA difference
    diff = np.abs(arr_orig - arr_comp)
    diff_gray = np.mean(diff, axis=2)
    
    max_diff = np.max(diff_gray)
    if max_diff > 0:
        ela_normalized = (diff_gray / max_diff) * 255.0
    else:
        ela_normalized = diff_gray
        
    # Analyze Variance
    h, w = diff_gray.shape
    step = max(h, w) // 16
    patch_means = []
    
    for y in range(0, h - step, step):
        for x in range(0, w - step, step):
            patch = ela_normalized[y:y+step, x:x+step]
            patch_means.append(np.mean(patch))
            
    if not patch_means:
        return _fallback()
        
    ela_std = float(np.std(patch_means))
    
    # Very weak scoring. Only extreme standard deviation triggers it.
    ela_anomaly = 0.0
    if ela_std > 50.0:
        ela_anomaly = 0.4
    if ela_std > 80.0:
        ela_anomaly = 0.6
        
    over_sharpening = _oversharp_cv(diff_gray.astype(np.uint8))

    return [
        {
            "signal_name": "ela_anomaly",
            "signal_strength": round(ela_anomaly, 3),
            "signal_type": "edit",
            "confidence": 0.5, # Low confidence auxiliary flag
            "source": "retouch"
        },
        {
            "signal_name": "over_sharpening",
            "signal_strength": round(over_sharpening, 3),
            "signal_type": "edit",
            "confidence": 0.5, # Low confidence auxiliary flag
            "source": "retouch"
        }
    ]

def _oversharp_cv(gray: np.ndarray) -> float:
    """Detect over-sharpening via Laplacian zero-crossing density."""
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    sign = np.sign(lap[:, 1:] * lap[:, :-1])
    zero_crossings = float(np.sum(sign < 0))
    density = zero_crossings / float(gray.size)
    if density > 0.2:
        return 0.5
    return 0.0

def _fallback() -> list:
    return [{
        "signal_name": "error",
        "signal_strength": 0.0,
        "signal_type": "error",
        "confidence": 0.0,
        "source": "retouch"
    }]

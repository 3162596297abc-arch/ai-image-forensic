"""Layer 3: Structural Collapse Detector — AI generation artifact detection."""
import numpy as np
import cv2

def analyze(image_bytes: bytes) -> list:
    """Detect localized structural collapse (edges, repetitions, high-frequency anomalies)."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            return _fallback()
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
    except Exception:
        return _fallback()

    # Calculate raw features
    fft_anomaly_score = _analyze_fft_anomalies(gray, h, w)
    edge_collapse_score = _analyze_edge_collapse(gray)
    local_repetition_score = _analyze_repetition(gray)

    # Return only if anomalies are STRONG.
    # To avoid false positives on commercial photography, we squash weak scores.
    
    fft_anomaly_score = fft_anomaly_score if fft_anomaly_score > 0.6 else 0.0
    edge_collapse_score = edge_collapse_score if edge_collapse_score > 0.65 else 0.0
    local_repetition_score = local_repetition_score if local_repetition_score > 0.7 else 0.0

    return [
        {
            "signal_name": "fft_abnormal_spikes",
            "signal_strength": round(fft_anomaly_score, 3),
            "signal_type": "structure",
            "confidence": 0.85,
            "source": "texture"
        },
        {
            "signal_name": "edge_collapse",
            "signal_strength": round(edge_collapse_score, 3),
            "signal_type": "structure",
            "confidence": 0.8,
            "source": "texture"
        },
        {
            "signal_name": "local_repetition",
            "signal_strength": round(local_repetition_score, 3),
            "signal_type": "structure",
            "confidence": 0.75,
            "source": "texture"
        }
    ]

def _analyze_fft_anomalies(gray: np.ndarray, h: int, w: int) -> float:
    """Use FFT to find unnatural frequency spikes typical of GAN/Diffusion upscaling."""
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    mag_spectrum = 20 * np.log(np.abs(fshift) + 1e-5)
    
    y, x = np.indices((h, w))
    center = np.array([h // 2, w // 2])
    r = np.hypot(x - center[1], y - center[0]).astype(int)
    
    max_radius = min(h // 2, w // 2)
    ring_means = np.zeros(max_radius)
    for i in range(max_radius):
        mask = (r == i)
        if np.any(mask):
            ring_means[i] = np.mean(mag_spectrum[mask])
            
    abnormal_spikes = int(np.sum(np.abs(np.diff(ring_means)) > 3.0))
    # >5 spikes is highly indicative of AI upscaler artifacts
    return min(1.0, abnormal_spikes / 10.0)

def _analyze_edge_collapse(gray: np.ndarray) -> float:
    """Check for 'forced edge fusion' where AI fails to separate overlapping objects."""
    edges = cv2.Canny(gray, 50, 150)
    # Dilate edges to find complex intersection regions
    kernel = np.ones((3,3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    
    # Count junction points (where multiple edges meet in a messy way)
    harris = cv2.cornerHarris(np.float32(dilated), 2, 3, 0.04)
    harris_dilated = cv2.dilate(harris, None)
    
    # Threshold for an optimal value
    corner_mask = harris_dilated > 0.01 * harris_dilated.max()
    corner_count = np.sum(corner_mask)
    
    # If there are too many localized messy corners in a small image, it's AI edge confusion
    total_pixels = gray.shape[0] * gray.shape[1]
    corner_density = corner_count / total_pixels
    
    # Highly empirical threshold for AI edge messiness
    if corner_density > 0.05:
        return 0.8
    if corner_density > 0.03:
        return 0.5
    return 0.0

def _analyze_repetition(gray: np.ndarray) -> float:
    """Detect repeating local texture patches (e.g. AI generating identical teeth or leaves)."""
    bh = max(1, gray.shape[0] // 8)
    bw = max(1, gray.shape[1] // 8)
    blocks = []
    for y in range(0, gray.shape[0] - bh, bh):
        for x in range(0, gray.shape[1] - bw, bw):
            block = gray[y:y + bh, x:x + bw]
            blocks.append(float(np.var(block)))
            
    if len(blocks) < 4:
        return 0.0
        
    # If standard deviation of block variances is extremely low, the texture is repeating artificially
    std_var = float(np.std(blocks))
    mean_var = float(np.mean(blocks)) + 1e-5
    
    cv_val = std_var / mean_var
    if cv_val < 0.2:
        return 0.85 # Extreme unnatural repetition
    if cv_val < 0.4:
        return 0.6
    return 0.0

def _fallback() -> list:
    return [{
        "signal_name": "error",
        "signal_strength": 0.0,
        "signal_type": "error",
        "confidence": 0.0,
        "source": "texture"
    }]

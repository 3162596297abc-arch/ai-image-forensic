"""Layer 2: Sensor Reality Detector — Camera Authenticity Modeling."""
import numpy as np
import cv2

def analyze(image_bytes: bytes) -> list:
    """Analyze camera sensor authenticity (CMOS Noise, Lens Blur, Sensor Randomness)."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            return _fallback()
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    except Exception:
        return _fallback()

    h, w = gray.shape
    
    cmos_noise_absence = _analyze_cmos_noise(gray)
    sensor_randomness_absence = _analyze_sensor_randomness(gray)
    lens_blur_anomaly = _analyze_lens_blur(gray, h)
    
    return [
        {
            "signal_name": "cmos_noise_absence",
            "signal_strength": round(cmos_noise_absence, 3),
            "signal_type": "sensor",
            "confidence": 0.9,
            "source": "physics"
        },
        {
            "signal_name": "sensor_randomness_absence",
            "signal_strength": round(sensor_randomness_absence, 3),
            "signal_type": "sensor",
            "confidence": 0.85,
            "source": "physics"
        },
        {
            "signal_name": "lens_blur_anomaly",
            "signal_strength": round(lens_blur_anomaly, 3),
            "signal_type": "sensor",
            "confidence": 0.8,
            "source": "physics"
        }
    ]

def _analyze_cmos_noise(gray: np.ndarray) -> float:
    """Real photos have high frequency CMOS noise. AI is mathematically smooth."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    noise = cv2.absdiff(gray, blur)
    noise_var = float(np.var(noise))
    
    # Real photos usually have variance > 5.0. 
    # If variance is < 1.0, it's artificially smoothed.
    if noise_var < 1.0:
        return 0.9 # Extreme absence of noise
    if noise_var > 15.0:
        return 0.1 # Very noisy, likely real
    
    return max(0.0, min(1.0, 1.0 - (noise_var / 15.0)))

def _analyze_sensor_randomness(gray: np.ndarray) -> float:
    """Real sensor noise is randomly distributed. AI noise (if added) is often patterned."""
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    lap_var = float(np.var(laplacian))
    lap_mean = float(np.mean(laplacian))
    
    # CV of laplacian. Real images have distinct high-freq randomness.
    cv_val = lap_var / (abs(lap_mean) + 1e-5)
    
    if cv_val < 100:
        return 0.8 # Too uniform
    if cv_val > 1000:
        return 0.1 # Highly random
        
    return max(0.0, min(1.0, 1.0 - (cv_val / 1000.0)))

def _analyze_lens_blur(gray: np.ndarray, h: int) -> float:
    """Check optical depth of field logic (background blur progression)."""
    zones = [
        gray[0:h // 3, :],
        gray[h // 3:2 * h // 3, :],
        gray[2 * h // 3:, :],
    ]
    vars = []
    for zone in zones:
        if zone.size > 0:
            lap = cv2.Laplacian(zone, cv2.CV_64F)
            vars.append(float(np.var(lap)))
            
    if len(vars) < 2:
        return 0.5
        
    # Real bokeh has a specific variance ratio. AI often gets it slightly wrong mathematically.
    std_vars = float(np.std(vars))
    mean_vars = float(np.mean(vars)) + 1e-5
    
    ratio = std_vars / mean_vars
    # AI often creates hyper-sharp subjects with perfectly blurred backgrounds (ratio too high)
    if ratio > 1.5:
        return 0.8
    if ratio < 0.2:
        return 0.7 # Flat image
        
    return 0.2

def _fallback() -> list:
    return [{
        "signal_name": "error",
        "signal_strength": 0.0,
        "signal_type": "error",
        "confidence": 0.0,
        "source": "physics"
    }]

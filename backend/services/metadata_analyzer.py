"""Metadata Analyzer Sensor for Truth Engine Lite."""
import io
from PIL import Image
from PIL.ExifTags import TAGS
from services.logger import AuditLogger

def analyze(image_bytes: bytes) -> list:
    """Analyze image metadata for missing EXIF data, a strong signal for AI-generated imagery."""
    
    # We default to 0 (real photo) and add penalty if EXIF is completely missing
    exif_missing_penalty = 0.0
    confidence = 0.85
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img.getexif()
        
        # A real photo taken by a camera will usually have some of these tags:
        # DateTimeOriginal, Make, Model, ISOSpeedRatings, FNumber, FocalLength
        has_real_exif = False
        
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                # Check for camera-specific hardware tags
                if tag_name in ['Make', 'Model', 'ISOSpeedRatings', 'FNumber', 'FocalLength']:
                    has_real_exif = True
                    break
        
        if not has_real_exif:
            # If no real EXIF hardware tags are found, we suspect it might be AI/Generated or heavily stripped
            exif_missing_penalty = 0.50
            
    except Exception as e:
        # Image couldn't be parsed for EXIF, treat as suspicious
        AuditLogger.log_trace("MetadataAnalyzer", "Exception", str(e), level="WARN")
        exif_missing_penalty = 0.50
        confidence = 0.50
        
    return [
        {
            "signal_name": "exif_missing",
            "signal_strength": exif_missing_penalty,
            "signal_type": "metadata",
            "confidence": confidence,
            "source": "metadata_analyzer"
        }
    ]

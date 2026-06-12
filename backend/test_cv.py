import sys
import os
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services import physics_engine, texture_analyzer, retouch_detector, aesthetic_drift, metadata_analyzer

def main():
    print("Generating test image...")
    # Create a simple test image with some texture
    img_np = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.randn(img_np, 128, 50) # Add noise
    cv2.circle(img_np, (256, 256), 100, (255, 255, 255), -1) # Add a circle
    
    img = Image.fromarray(img_np)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=95)
    img_bytes = buf.getvalue()
    
    print("\n--- Testing physics_engine ---")
    print(physics_engine.analyze(img_bytes))
    
    print("\n--- Testing texture_analyzer ---")
    print(texture_analyzer.analyze(img_bytes))
    
    print("\n--- Testing retouch_detector ---")
    print(retouch_detector.analyze(img_bytes))
    
    print("\n--- Testing aesthetic_drift ---")
    print(aesthetic_drift.analyze(img_bytes))
    
    print("\n--- Testing metadata_analyzer ---")
    print(metadata_analyzer.analyze(img_bytes))

if __name__ == "__main__":
    main()

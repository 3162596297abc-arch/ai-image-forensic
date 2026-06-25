"""Metadata Analyzer（v4 重构）。

关键修复：从 raw_bytes（原始上传字节）读 EXIF。
旧版被喂预处理后的 PNG，EXIF 早被剥光 → 每张图(含真相机照)恒判"无 EXIF"。
现在从原图读，至少能正确反映真实情况。
注意：EXIF 缺失是【弱信号】——大量正规网络图片会被平台剥离元数据，
因此本信号只作为辅助参考，fusion 不会用它单独驱动判定，避免大面积假阳性。
"""
import io
from PIL import Image
from PIL.ExifTags import TAGS
from services.logger import AuditLogger

_CAMERA_TAGS = {"Make", "Model", "ISOSpeedRatings", "FNumber", "FocalLength", "DateTimeOriginal", "LensModel"}


def analyze(views: dict) -> list:
    raw_bytes = views.get("raw_bytes")
    exif_missing_penalty = 0.0
    confidence = 0.4  # 整体降信度：EXIF 缺失不可靠

    try:
        img = Image.open(io.BytesIO(raw_bytes))
        exif_data = img.getexif()
        has_real_exif = False
        if exif_data:
            for tag_id in exif_data:
                if TAGS.get(tag_id, tag_id) in _CAMERA_TAGS:
                    has_real_exif = True
                    break
        if not has_real_exif:
            exif_missing_penalty = 0.50
    except Exception as e:
        AuditLogger.log_trace("MetadataAnalyzer", "Exception", str(e), level="WARN")
        exif_missing_penalty = 0.50
        confidence = 0.3

    return [
        {"signal_name": "exif_missing", "signal_strength": exif_missing_penalty,
         "signal_type": "metadata", "confidence": confidence, "source": "metadata_analyzer"},
    ]

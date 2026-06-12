"""Centralized Observability and Auditing Logger."""
import json
import logging
import os
from datetime import datetime

# Setup standard python logging for console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
console_logger = logging.getLogger("TruthEngine")

# Setup audit log file path
AUDIT_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evidence_audit.log")

class AuditLogger:
    """Handles structured JSON logging for full-chain traceability."""
    
    @staticmethod
    def log_trace(analysis_id: str, stage: str, data: dict, level: str = "INFO"):
        """Log a specific stage of the pipeline."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "analysis_id": analysis_id,
            "level": level,
            "stage": stage,
            "data": data
        }
        
        # Write to JSONL audit file
        try:
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            console_logger.error(f"Failed to write to audit log: {e}")
            
        # Also print to console
        console_message = f"[{analysis_id}] {stage}: {json.dumps(data, ensure_ascii=False)[:200]}..."
        if level == "ERROR":
            console_logger.error(console_message)
        elif level == "WARN":
            console_logger.warning(console_message)
        else:
            console_logger.info(console_message)

    @staticmethod
    def log_error(analysis_id: str, stage: str, error_msg: str, traceback_str: str = ""):
        """Log exceptions and degradation events."""
        AuditLogger.log_trace(
            analysis_id=analysis_id,
            stage=stage,
            data={"error": error_msg, "traceback": traceback_str},
            level="ERROR"
        )

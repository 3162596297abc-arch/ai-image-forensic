"""Jury Orchestrator — High-availability scheduler with Circuit Breaker and Timeouts."""
import asyncio
import time
from services.logger import AuditLogger
from services.texture_analyzer import analyze as texture_analyze
from services.physics_engine import analyze as physics_analyze
from services.retouch_detector import analyze as retouch_analyze
from services.metadata_analyzer import analyze as metadata_analyze

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED (healthy), OPEN (tripped), HALF_OPEN (testing)
        self.last_failure_time = 0.0

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            self.last_failure_time = time.time()
            AuditLogger.log_trace("SYSTEM", "CircuitBreaker", {"module": self.name, "action": "TRIPPED"}, level="WARN")

    def record_success(self):
        self.failures = 0
        if self.state != "CLOSED":
            self.state = "CLOSED"
            AuditLogger.log_trace("SYSTEM", "CircuitBreaker", {"module": self.name, "action": "RESTORED"}, level="INFO")

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            # Check if enough time has passed to try recovery
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        # HALF_OPEN allows 1 test execution
        return True

JURY_MODULES = [
    {"name": "Structural Collapse Detector", "fn": texture_analyze, "desc": "Detecting localized structural generation failures...", "breaker": CircuitBreaker("Structural Collapse Detector")},
    {"name": "Sensor Reality Detector", "fn": physics_analyze, "desc": "Modeling real camera sensor authenticity...", "breaker": CircuitBreaker("Sensor Reality Detector")},
    {"name": "Auxiliary Retouch Detector", "fn": retouch_analyze, "desc": "Detecting minor post-processing anomalies...", "breaker": CircuitBreaker("Auxiliary Retouch Detector")},
    {"name": "Metadata Analyzer", "fn": metadata_analyze, "desc": "Scanning for hardware EXIF anomalies...", "breaker": CircuitBreaker("Metadata Analyzer")},
]

async def _run_module_with_timeout(analysis_id: str, module: dict, image_bytes: bytes, timeout: float = 15.0) -> dict:
    breaker: CircuitBreaker = module["breaker"]
    
    if not breaker.can_execute():
        AuditLogger.log_trace(analysis_id, "ModuleSkipped", {"module": module["name"], "reason": "Circuit Breaker OPEN"}, level="WARN")
        return {"module": module["name"], "features": {"error": "CIRCUIT_BREAKER_OPEN", "confidence": 0.0}}, "skipped"

    try:
        # Run CPU-bound OpenCV tasks in thread pool
        result = await asyncio.wait_for(
            asyncio.to_thread(module["fn"], image_bytes),
            timeout=timeout
        )
        breaker.record_success()
        return result, "complete"
    except asyncio.TimeoutError:
        breaker.record_failure()
        AuditLogger.log_trace(analysis_id, "ModuleTimeout", {"module": module["name"], "timeout": timeout}, level="WARN")
        return {"module": module["name"], "features": {"error": "TIMEOUT", "confidence": 0.0}}, "timeout"
    except Exception as e:
        breaker.record_failure()
        AuditLogger.log_error(analysis_id, "ModuleException", f"Module {module['name']} failed: {str(e)}")
        return {"module": module["name"], "features": {"error": f"Exception: {str(e)[:50]}", "confidence": 0.0}}, "error"

async def run_jury(analysis_id: str, image_bytes: bytes) -> dict:
    """Run all detection modules concurrently with timeouts and circuit breakers."""
    results = []
    jury_phases = []

    # Dispatch all modules concurrently
    tasks = [
        _run_module_with_timeout(analysis_id, module, image_bytes, timeout=15.0)
        for module in JURY_MODULES
    ]
    
    completed_tasks = await asyncio.gather(*tasks)

    for i, (result, status) in enumerate(completed_tasks):
        results.append(result)
        jury_phases.append({
            "name": JURY_MODULES[i]["name"],
            "desc": JURY_MODULES[i]["desc"],
            "status": status,
        })

    return {
        "module_results": results,
        "jury_phases": jury_phases,
    }

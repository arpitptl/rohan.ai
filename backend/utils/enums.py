from enum import Enum

class PredictionType(Enum):
    DOWNTIME = "downtime"
    MAINTENANCE = "maintenance"
    DEGRADATION = "degradation"

class FIPStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical" 
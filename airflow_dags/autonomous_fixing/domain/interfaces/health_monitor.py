"""Health monitor interface."""

from abc import ABC, abstractmethod
from ..models import HealthMetrics


class IHealthMonitor(ABC):
    """
    Interface for health monitoring.

    Implementations can use different strategies:
    - Smart tiered checking (static → dynamic only when needed)
    - Full health check always
    - Cached health metrics
    """

    @abstractmethod
    def check_health(self, force_dynamic: bool = False) -> HealthMetrics:
        """
        Check project health.

        Args:
            force_dynamic: Force dynamic checks even if static passes

        Returns:
            HealthMetrics with static and optionally dynamic data
        """
        pass

    @abstractmethod
    def calculate_overall_health(self, metrics: HealthMetrics) -> float:
        """
        Calculate overall health score.

        Args:
            metrics: Health metrics

        Returns:
            Overall health score (0.0 - 1.0)
        """
        pass

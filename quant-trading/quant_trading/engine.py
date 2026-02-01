"""Decision engine that orchestrates strategies and risk management."""

from dataclasses import dataclass
from decimal import Decimal

from quant_trading.models import MarketContext, Signal
from quant_trading.risk import RiskManager, ValidationResult
from quant_trading.strategy import Strategy, StrategyRegistry


@dataclass
class Recommendation:
    """A validated trading recommendation."""

    signal: Signal
    validation: ValidationResult
    approved: bool
    adjusted_size: Decimal | None = None

    @property
    def rejection_reason(self) -> str | None:
        """Get reason for rejection if not approved."""
        if self.approved:
            return None
        return self.validation.reason


class DecisionEngine:
    """Orchestrates strategy execution and risk validation."""

    def __init__(
        self,
        registry: StrategyRegistry,
        risk_manager: RiskManager,
        active_strategy: str,
        confidence_threshold: int = 70,
    ) -> None:
        self.registry = registry
        self.risk_manager = risk_manager
        self.active_strategy = active_strategy
        self.confidence_threshold = confidence_threshold

    def get_strategy(self) -> Strategy:
        """Get the currently active strategy."""
        return self.registry.get(self.active_strategy)

    def analyze(self, context: MarketContext) -> list[Recommendation]:
        """Run analysis and return validated recommendations."""
        strategy = self.get_strategy()
        signals = strategy.analyze(context)

        recommendations = []
        for signal in signals:
            # Filter by confidence threshold
            if signal.confidence < self.confidence_threshold:
                continue

            # Validate against risk rules
            validation = self.risk_manager.validate_signal(signal, context)

            recommendation = Recommendation(
                signal=signal,
                validation=validation,
                approved=validation.allowed,
                adjusted_size=validation.adjusted_size,
            )
            recommendations.append(recommendation)

        return recommendations

    def set_active_strategy(self, name: str) -> None:
        """Change the active strategy."""
        # Verify it exists
        self.registry.get(name)
        self.active_strategy = name

    def set_confidence_threshold(self, threshold: int) -> None:
        """Update the confidence threshold."""
        if not 0 <= threshold <= 100:
            raise ValueError("Threshold must be between 0 and 100")
        self.confidence_threshold = threshold

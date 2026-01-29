"""Custom exceptions for the quant trading system."""


class QuantError(Exception):
    """Base exception for quant system errors."""

    pass


class BrokerError(QuantError):
    """Exception raised when broker operations fail."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class BrokerConnectionError(BrokerError):
    """Exception raised when broker connection fails."""

    pass


class BrokerOrderError(BrokerError):
    """Exception raised when order submission fails."""

    pass

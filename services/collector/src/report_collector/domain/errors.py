class CollectorError(RuntimeError):
    """Base exception for expected collector failures."""


class SourceParseError(CollectorError):
    """Raised when required public HTML structure is unavailable."""


class SourceMaintenanceError(CollectorError):
    """Raised when an official source explicitly reports scheduled maintenance."""


class SourceTimeoutError(CollectorError):
    """Raised when a source request or execution times out."""


class FileValidationError(CollectorError):
    """Raised when a downloaded attachment is unsafe or invalid."""


class InvalidTransitionError(CollectorError):
    """Raised when a workflow state transition is not allowed."""

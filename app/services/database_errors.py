# app/services/database_errors.py - Centralized database error mapping
# Maps SQLAlchemy exceptions to business-level ServiceError codes
import logging

from sqlalchemy.exc import (
    DataError,
    DisconnectionError,
    IntegrityError,
    OperationalError,
    ProgrammingError,
    SQLAlchemyError,
)
from sqlalchemy.exc import (
    TimeoutError as SQLAlchemyTimeoutError,
)
from sqlalchemy.orm.exc import StaleDataError

from app.services.errors import ServiceError

logger = logging.getLogger(__name__)


class DatabaseErrorMapper:
    """Maps SQLAlchemy exceptions to business-level ServiceError codes."""

    @staticmethod
    def map_database_error(
        error: SQLAlchemyError,
        entity_name: str,
        operation: str = "operation",
    ) -> ServiceError:
        """Convert database exception to ServiceError with appropriate code.

        Args:
            error: The SQLAlchemy exception caught
            entity_name: Name of entity (for logging), e.g., "User", "Role"
            operation: Type of operation ("create", "update", "delete")

        Returns:
            ServiceError with appropriate code for HTTP mapping

        Mapping:
            - IntegrityError → conflict (409) if key/FK, validation_error (400) if check/not null
            - StaleDataError → conflict (409) optimistic locking
            - DataError → validation_error (400)
            - OperationalError → service_error (500)
            - ProgrammingError → service_error (500)
            - DisconnectionError → service_error (500)
            - TimeoutError → service_error (500)
            - Other → service_error (500)
        """
        if isinstance(error, IntegrityError):
            # Integrity errors can be conflicts (duplicate key, FK violation)
            # or validation errors (NOT NULL, CHECK constraint)
            message = str(error.orig) if error.orig else str(error)

            if any(keyword in message.lower() for keyword in ["unique", "duplicate", "key"]):
                logger.warning(
                    "Duplicate key error on %s %s: %s",
                    entity_name,
                    operation,
                    message,
                )
                return ServiceError(
                    f"Duplicate {entity_name.lower()}: resource already exists",
                    code="conflict",
                )

            if any(keyword in message.lower() for keyword in ["foreign key", "fk violation"]):
                logger.warning(
                    "Foreign key violation on %s %s: %s",
                    entity_name,
                    operation,
                    message,
                )
                return ServiceError(
                    f"Cannot {operation} {entity_name.lower()}: referenced resource not found",
                    code="conflict",
                )

            if any(keyword in message.lower() for keyword in ["not null", "null constraint"]):
                logger.warning(
                    "NOT NULL constraint violation on %s %s: %s",
                    entity_name,
                    operation,
                    message,
                )
                return ServiceError(
                    f"Required field missing on {entity_name.lower()}",
                    code="validation_error",
                )

            if any(keyword in message.lower() for keyword in ["check constraint"]):
                logger.warning(
                    "CHECK constraint violation on %s %s: %s",
                    entity_name,
                    operation,
                    message,
                )
                return ServiceError(
                    f"Invalid data for {entity_name.lower()}",
                    code="validation_error",
                )

            # Default IntegrityError → conflict
            logger.error("Integrity error on %s %s: %s", entity_name, operation, message)
            return ServiceError(
                f"Data conflict on {entity_name.lower()}",
                code="conflict",
            )

        elif isinstance(error, StaleDataError):
            logger.warning("Stale data (optimistic lock) on %s %s", entity_name, operation)
            return ServiceError(
                f"{entity_name} was modified by another transaction",
                code="conflict",
            )

        elif isinstance(error, DataError):
            logger.warning("Data error on %s %s: %s", entity_name, operation, str(error))
            return ServiceError(
                f"Invalid data type or format for {entity_name.lower()}",
                code="validation_error",
            )

        elif isinstance(error, ProgrammingError):
            logger.error(
                "Programming error on %s %s (SQL or permission issue): %s",
                entity_name,
                operation,
                str(error),
            )
            return ServiceError(
                "Database operation failed due to SQL or permission error",
                code="service_error",
            )

        elif isinstance(error, OperationalError):
            logger.error(
                "Operational error on %s %s (connection, deadlock, etc): %s",
                entity_name,
                operation,
                str(error),
            )
            return ServiceError(
                "Database temporarily unavailable, please try again",
                code="service_error",
            )

        elif isinstance(error, DisconnectionError):
            logger.error(
                "Disconnection error on %s %s: database connection lost", entity_name, operation
            )
            return ServiceError(
                "Database connection lost, please try again",
                code="service_error",
            )

        elif isinstance(error, SQLAlchemyTimeoutError):
            logger.error("Query timeout on %s %s", entity_name, operation)
            return ServiceError(
                "Query timeout, please try again",
                code="service_error",
            )

        else:
            # Unknown SQLAlchemy error
            logger.error(
                "Unknown SQLAlchemy error on %s %s: %s",
                entity_name,
                operation,
                str(error),
            )
            return ServiceError(
                "Unexpected database error",
                code="service_error",
            )

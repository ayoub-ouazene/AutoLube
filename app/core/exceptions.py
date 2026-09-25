"""Application errors mapped to consistent HTTP responses."""


class AppError(Exception):
    """Base for all application-level errors."""

    http_status = 500
    default_message = "Une erreur interne est survenue."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class RateLimitError(AppError):
    http_status = 429
    default_message = "Service occupé, veuillez réessayer dans un instant."


class ProviderUnavailableError(AppError):
    http_status = 503
    default_message = "Le service de recherche est temporairement indisponible."


class ProviderTimeoutError(AppError):
    http_status = 504
    default_message = "Le service de recherche a mis trop de temps à répondre."


class DatabaseError(AppError):
    http_status = 503
    default_message = "Base de données temporairement indisponible."


class AuthError(AppError):
    http_status = 401
    default_message = "Identifiants invalides."


class NotFoundError(AppError):
    http_status = 404
    default_message = "Ressource introuvable."


class ValidationError(AppError):
    http_status = 400
    default_message = "Requête invalide."

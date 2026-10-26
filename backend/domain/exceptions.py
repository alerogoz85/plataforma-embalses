"""Excepciones de dominio. Centralizan las reglas de negocio que pueden violarse."""


class DomainError(Exception):
    """Excepcion base para todos los errores del dominio hidrologico."""


class VolumenInvalidoError(DomainError):
    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)


class CaudalInvalidoError(DomainError):
    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)


class EmbalseNoEncontradoError(DomainError):
    def __init__(self, embalse_id: str) -> None:
        super().__init__(f"No existe un embalse con identificador '{embalse_id}'")
        self.embalse_id = embalse_id


class SinMedicionesError(DomainError):
    def __init__(self, embalse_id: str) -> None:
        super().__init__(f"El embalse '{embalse_id}' no tiene mediciones registradas")
        self.embalse_id = embalse_id


class DatosHistoricosInsuficientesError(DomainError):
    def __init__(self, embalse_id: str, requeridos: int, disponibles: int) -> None:
        super().__init__(
            f"El embalse '{embalse_id}' requiere al menos {requeridos} registros "
            f"historicos para generar una prediccion confiable, tiene {disponibles}"
        )
        self.embalse_id = embalse_id
        self.requeridos = requeridos
        self.disponibles = disponibles


class EsquemaIncompatibleError(DomainError):
    def __init__(self, detalle: str) -> None:
        super().__init__(detalle)


class FuenteDatosError(DomainError):
    """Falla al obtener o interpretar datos de una fuente externa."""


class ModeloCarbonNoCargadoError(DomainError):
    """No se ha importado ninguna corrida del modelo de carbon termico."""

    def __init__(self) -> None:
        super().__init__(
            "El modelo de carbon termico aun no esta cargado; ejecuta "
            "infrastructure.ingesta.importar_modelo_carbon"
        )


class ModeloDnsNoCargadoError(DomainError):
    """No se ha importado ninguna corrida del modelo de demanda no atendida (DNS)."""

    def __init__(self) -> None:
        super().__init__(
            "El modelo DNS aun no esta cargado; ejecuta infrastructure.ingesta.importar_modelo_dns"
        )


class FiltroInvalidoError(DomainError):
    """Un filtro pide una region o subarea que no existe en el modelo cargado."""

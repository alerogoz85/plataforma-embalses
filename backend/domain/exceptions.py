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


class ModeloNoEncontradoError(DomainError):
    """El modelo pedido no es uno de los tableros de modelos analiticos."""

    def __init__(self, modelo_id: str) -> None:
        super().__init__(f"El modelo '{modelo_id}' no existe")


class EscenarioNoDisponibleError(DomainError):
    """No se ha importado la tanda de escenarios del visor de apagon (o no trae esa combinacion)."""

    def __init__(self) -> None:
        super().__init__("Aun no hay escenarios importados para esa combinacion de controles")


# --- Modulo de actualizacion de tableros (seguridad y carga de archivos) ---------------------------------
class CredencialesInvalidasError(DomainError):
    """Usuario o contraseña incorrectos. El mensaje es el mismo exista o no el usuario (no revela cuentas)."""

    def __init__(self) -> None:
        super().__init__("Usuario o contraseña incorrectos")


class CuentaBloqueadaError(DomainError):
    def __init__(self, minutos: int) -> None:
        super().__init__(f"Demasiados intentos fallidos. Intenta de nuevo en {minutos} minutos")
        self.minutos = minutos


class SesionInvalidaError(DomainError):
    """Sin sesion, sesion vencida o token CSRF incorrecto."""

    def __init__(self, mensaje: str = "Debes iniciar sesión para continuar") -> None:
        super().__init__(mensaje)


class AccesoDenegadoError(DomainError):
    def __init__(self, mensaje: str = "No tienes permiso para esta acción") -> None:
        super().__init__(mensaje)


class TableroNoActualizableError(DomainError):
    def __init__(self, tablero_id: str) -> None:
        super().__init__(f"El tablero '{tablero_id}' no se actualiza con este módulo")


class CargaInvalidaError(DomainError):
    """Los archivos recibidos no cumplen: formato, tamaño, contenido o estructura. Lleva la lista de motivos."""

    def __init__(self, errores: list[str]) -> None:
        super().__init__("; ".join(errores))
        self.errores = errores


class AlmacenamientoNoPersistenteError(DomainError):
    """Se intento guardar en un entorno donde lo escrito se perderia (p. ej. Vercel sin base externa)."""

    def __init__(self) -> None:
        super().__init__("Este entorno no tiene almacenamiento persistente: configura DATABASE_URL para poder actualizar los tableros")

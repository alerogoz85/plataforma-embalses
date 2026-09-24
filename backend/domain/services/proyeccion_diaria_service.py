from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

VALOR_MINIMO_PCT = 0.0
VALOR_MAXIMO_PCT = 100.0
DIA_DEL_MES_DE_LA_ANCLA = 15


@dataclass(frozen=True, slots=True)
class AnclaMensual:
    """Valor mensual proyectado (promedio del mes) situado a mitad de mes."""

    fecha: date
    limite_inferior: float
    valor_esperado: float
    limite_superior: float

    @staticmethod
    def de_mes(mes: date, limite_inferior: float, valor_esperado: float, limite_superior: float) -> "AnclaMensual":
        return AnclaMensual(
            mes.replace(day=DIA_DEL_MES_DE_LA_ANCLA), limite_inferior, valor_esperado, limite_superior
        )


@dataclass(frozen=True, slots=True)
class PuntoDiario:
    fecha: date
    limite_inferior: float
    valor_esperado: float
    limite_superior: float


class ProyeccionDiariaService:
    """Convierte una proyeccion mensual en una serie diaria por interpolacion lineal.

    Arranca en el ultimo valor observado (sin incertidumbre) y pasa por cada valor
    mensual, tratado como el promedio de su mes y situado a mitad de mes. Solo
    cubre hasta la ultima ancla: no extrapola mas alla de lo publicado.
    """

    @staticmethod
    def interpolar(
        ultima_fecha: date,
        ultimo_valor: float,
        anclas: list[AnclaMensual],
        horizonte_dias: int,
    ) -> list[PuntoDiario]:
        futuras = sorted((a for a in anclas if a.fecha > ultima_fecha), key=lambda a: a.fecha)
        if not futuras:
            return []
        nodos = [AnclaMensual(ultima_fecha, ultimo_valor, ultimo_valor, ultimo_valor), *futuras]

        puntos: list[PuntoDiario] = []
        tramo = 0
        for dia in range(1, horizonte_dias + 1):
            fecha = ultima_fecha + timedelta(days=dia)
            if fecha > nodos[-1].fecha:
                break
            while fecha > nodos[tramo + 1].fecha:
                tramo += 1
            a, b = nodos[tramo], nodos[tramo + 1]
            t = (fecha - a.fecha).days / (b.fecha - a.fecha).days
            puntos.append(
                PuntoDiario(
                    fecha=fecha,
                    limite_inferior=_acotar(a.limite_inferior + t * (b.limite_inferior - a.limite_inferior)),
                    valor_esperado=_acotar(a.valor_esperado + t * (b.valor_esperado - a.valor_esperado)),
                    limite_superior=_acotar(a.limite_superior + t * (b.limite_superior - a.limite_superior)),
                )
            )
        return puntos


def _acotar(valor: float) -> float:
    return max(VALOR_MINIMO_PCT, min(VALOR_MAXIMO_PCT, valor))

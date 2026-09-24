"""Clientes HTTP finos para las APIs publicas de XM. Solo obtienen datos
crudos; la interpretacion vive en simem_xm_fuente.py para poder probarla sin red."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from domain.exceptions import FuenteDatosError

URL_SIMEM = "https://www.simem.co/backend-files/api/datos-publicos"
URL_XM = "https://servapibi.xm.com.co"
TIMEOUT_SEGUNDOS = 600
# La API diaria de XM rechaza rangos de mas de ~31 dias por consulta.
DIAS_POR_CONSULTA_XM = 30


def _crear_sesion() -> requests.Session:
    sesion = requests.Session()
    reintentos = Retry(
        total=4,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
    )
    sesion.mount("https://", HTTPAdapter(max_retries=reintentos))
    return sesion


class ClienteSimem:
    """API publica de SIMEM: un dataset por consulta, sin autenticacion."""

    def __init__(self, sesion: requests.Session | None = None) -> None:
        self._sesion = sesion or _crear_sesion()

    def consultar(self, dataset_id: str, desde: date, hasta: date) -> list[dict[str, Any]]:
        try:
            respuesta = self._sesion.post(
                URL_SIMEM,
                params={
                    "datasetId": dataset_id,
                    "startDate": desde.isoformat(),
                    "endDate": hasta.isoformat(),
                },
                json=[],
                timeout=TIMEOUT_SEGUNDOS,
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
        except (requests.RequestException, ValueError) as error:
            raise FuenteDatosError(f"SIMEM dataset {dataset_id}: {error}") from error
        if not isinstance(datos, list):
            raise FuenteDatosError(f"SIMEM dataset {dataset_id}: respuesta inesperada")
        return datos


class ClienteXm:
    """API clasica de XM (servapibi): metricas diarias y listados."""

    def __init__(self, sesion: requests.Session | None = None) -> None:
        self._sesion = sesion or _crear_sesion()

    def listar_embalses(self) -> list[dict[str, str]]:
        """Devuelve [{'Code', 'Name', 'HydroRegion'}, ...] sin repetidos."""
        try:
            respuesta = self._sesion.post(
                f"{URL_XM}/lists", json={"MetricId": "ListadoEmbalses"}, timeout=120
            )
            respuesta.raise_for_status()
            items = respuesta.json()["Items"]
        except (requests.RequestException, ValueError, KeyError) as error:
            raise FuenteDatosError(f"XM ListadoEmbalses: {error}") from error

        unicos: dict[str, dict[str, str]] = {}
        for item in items:
            for entidad in item["ListEntities"]:
                valores = entidad["Values"]
                unicos[valores["Code"]] = valores
        return list(unicos.values())

    def metrica_diaria_embalses(
        self, metrica: str, desde: date, hasta: date
    ) -> list[dict[str, Any]]:
        """Devuelve [{'Date', 'Name', 'Value'}, ...] recorriendo el rango en
        bloques permitidos por la API."""
        filas: list[dict[str, Any]] = []
        inicio = desde
        while inicio <= hasta:
            fin = min(inicio + timedelta(days=DIAS_POR_CONSULTA_XM - 1), hasta)
            filas.extend(self._consultar_bloque(metrica, inicio, fin))
            inicio = fin + timedelta(days=1)
        return filas

    def _consultar_bloque(self, metrica: str, desde: date, hasta: date) -> list[dict[str, Any]]:
        try:
            respuesta = self._sesion.post(
                f"{URL_XM}/daily",
                json={
                    "MetricId": metrica,
                    "Entity": "Embalse",
                    "StartDate": desde.isoformat(),
                    "EndDate": hasta.isoformat(),
                },
                timeout=TIMEOUT_SEGUNDOS,
            )
            respuesta.raise_for_status()
            items = respuesta.json()["Items"]
        except (requests.RequestException, ValueError, KeyError) as error:
            raise FuenteDatosError(f"XM {metrica} {desde}..{hasta}: {error}") from error

        return [
            {"Date": item["Date"], "Name": entidad["Name"], "Value": entidad["Value"]}
            for item in items
            for entidad in item["DailyEntities"]
        ]

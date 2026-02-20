"""
notion_automation.py
Core module for automating Notion database operations for Sexto Semestre de Software.
"""

import os
from datetime import date
from typing import Optional

from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

load_dotenv()

# ── Materias del 6to semestre de Ingeniería de Software ─────────────────────
MATERIAS_6TO = [
    "Ingeniería de Software",
    "Bases de Datos Avanzadas",
    "Redes y Comunicaciones",
    "Arquitectura de Software",
    "Seguridad Informática",
    "Proyecto Integrador",
    "Otra",
]

# Tipos de entrada soportados
TIPOS_ENTRADA = [
    "Tarea",
    "Examen",
    "Proyecto",
    "Apunte",
    "Recurso",
    "Actividad",
]

# Opciones de estado
ESTADOS = [
    "Por hacer",
    "En progreso",
    "Completado",
    "Cancelado",
]

# Opciones de prioridad
PRIORIDADES = [
    "Alta",
    "Media",
    "Baja",
]


class NotionAutomation:
    """Interface for automating Notion database entries for Sexto Semestre."""

    def __init__(
        self,
        token: Optional[str] = None,
        database_id: Optional[str] = None,
    ) -> None:
        self.token = token or os.getenv("NOTION_TOKEN")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")

        if not self.token:
            raise ValueError(
                "NOTION_TOKEN no encontrado. "
                "Configúralo en el archivo .env o pásalo como parámetro."
            )
        if not self.database_id:
            raise ValueError(
                "NOTION_DATABASE_ID no encontrado. "
                "Configúralo en el archivo .env o pásalo como parámetro."
            )

        self.client = Client(auth=self.token)

    # ── Operaciones de base de datos ─────────────────────────────────────────

    def agregar_entrada(
        self,
        titulo: str,
        materia: str = "Otra",
        tipo: str = "Tarea",
        estado: str = "Por hacer",
        prioridad: str = "Media",
        descripcion: str = "",
        fecha_limite: Optional[str] = None,
    ) -> dict:
        """
        Agrega una nueva entrada a la base de datos de Notion.

        Args:
            titulo: Nombre/título de la entrada.
            materia: Materia del 6to semestre a la que pertenece.
            tipo: Tipo de entrada (Tarea, Examen, Proyecto, etc.).
            estado: Estado actual (Por hacer, En progreso, etc.).
            prioridad: Prioridad (Alta, Media, Baja).
            descripcion: Descripción opcional adicional.
            fecha_limite: Fecha límite en formato YYYY-MM-DD (opcional).

        Returns:
            La página de Notion creada (dict).
        """
        if materia not in MATERIAS_6TO:
            materia = "Otra"
        if tipo not in TIPOS_ENTRADA:
            tipo = "Tarea"
        if estado not in ESTADOS:
            estado = "Por hacer"
        if prioridad not in PRIORIDADES:
            prioridad = "Media"

        properties: dict = {
            "Nombre": {
                "title": [{"text": {"content": titulo}}]
            },
            "Materia": {
                "select": {"name": materia}
            },
            "Tipo": {
                "select": {"name": tipo}
            },
            "Estado": {
                "select": {"name": estado}
            },
            "Prioridad": {
                "select": {"name": prioridad}
            },
        }

        if descripcion:
            properties["Descripción"] = {
                "rich_text": [{"text": {"content": descripcion}}]
            }

        if fecha_limite:
            properties["Fecha Límite"] = {
                "date": {"start": fecha_limite}
            }

        try:
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
            )
            return page
        except APIResponseError as exc:
            raise RuntimeError(
                f"Error al crear la entrada en Notion: {exc}"
            ) from exc

    def listar_entradas(
        self,
        materia: Optional[str] = None,
        estado: Optional[str] = None,
        tipo: Optional[str] = None,
    ) -> list[dict]:
        """
        Lista las entradas de la base de datos con filtros opcionales.

        Args:
            materia: Filtra por materia.
            estado: Filtra por estado.
            tipo: Filtra por tipo de entrada.

        Returns:
            Lista de páginas de Notion que coinciden con los filtros.
        """
        filtros: list[dict] = []

        if materia:
            filtros.append(
                {"property": "Materia", "select": {"equals": materia}}
            )
        if estado:
            filtros.append(
                {"property": "Estado", "select": {"equals": estado}}
            )
        if tipo:
            filtros.append(
                {"property": "Tipo", "select": {"equals": tipo}}
            )

        query_params: dict = {"database_id": self.database_id}
        if filtros:
            query_params["filter"] = (
                filtros[0] if len(filtros) == 1 else {"and": filtros}
            )

        try:
            response = self.client.databases.query(**query_params)
            return response.get("results", [])
        except APIResponseError as exc:
            raise RuntimeError(
                f"Error al consultar la base de datos de Notion: {exc}"
            ) from exc

    def actualizar_estado(self, page_id: str, nuevo_estado: str) -> dict:
        """
        Actualiza el estado de una entrada existente.

        Args:
            page_id: ID de la página de Notion.
            nuevo_estado: Nuevo estado a asignar.

        Returns:
            La página actualizada (dict).
        """
        if nuevo_estado not in ESTADOS:
            raise ValueError(
                f"Estado inválido '{nuevo_estado}'. "
                f"Opciones: {', '.join(ESTADOS)}"
            )

        try:
            page = self.client.pages.update(
                page_id=page_id,
                properties={
                    "Estado": {"select": {"name": nuevo_estado}}
                },
            )
            return page
        except APIResponseError as exc:
            raise RuntimeError(
                f"Error al actualizar la entrada en Notion: {exc}"
            ) from exc

    def eliminar_entrada(self, page_id: str) -> dict:
        """
        Archiva (elimina) una entrada de la base de datos.

        Args:
            page_id: ID de la página de Notion.

        Returns:
            La página archivada (dict).
        """
        try:
            page = self.client.pages.update(
                page_id=page_id,
                archived=True,
            )
            return page
        except APIResponseError as exc:
            raise RuntimeError(
                f"Error al archivar la entrada en Notion: {exc}"
            ) from exc

    def obtener_titulo(self, page: dict) -> str:
        """Extrae el título de texto de una página de Notion."""
        try:
            return (
                page["properties"]["Nombre"]["title"][0]["text"]["content"]
            )
        except (KeyError, IndexError):
            return "(sin título)"

    def obtener_propiedad_select(self, page: dict, propiedad: str) -> str:
        """Extrae el valor de una propiedad de tipo select."""
        try:
            return page["properties"][propiedad]["select"]["name"]
        except (KeyError, TypeError):
            return ""

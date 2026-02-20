"""
tests/test_notion_automation.py
Unit tests for the NotionAutomation module.
All tests mock the Notion API so no real credentials are needed.
"""

import pytest
from unittest.mock import MagicMock, patch, call

from notion_automation import (
    ESTADOS,
    MATERIAS_6TO,
    PRIORIDADES,
    TIPOS_ENTRADA,
    NotionAutomation,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def mock_notion_client():
    """Returns a patched notion_client.Client instance."""
    with patch("notion_automation.Client") as MockClient:
        instance = MockClient.return_value
        yield instance


@pytest.fixture()
def automation(mock_notion_client):
    """Returns a NotionAutomation instance backed by the mock client."""
    return NotionAutomation(token="secret_test", database_id="db_test_id")


# ── Constructor ───────────────────────────────────────────────────────────────

def test_missing_token_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="NOTION_TOKEN"):
            NotionAutomation(token=None, database_id="db_id")


def test_missing_database_id_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="NOTION_DATABASE_ID"):
            NotionAutomation(token="secret_test", database_id=None)


def test_constructor_uses_env_vars():
    env = {"NOTION_TOKEN": "secret_env", "NOTION_DATABASE_ID": "env_db_id"}
    with patch.dict("os.environ", env, clear=False):
        with patch("notion_automation.Client"):
            na = NotionAutomation()
            assert na.token == "secret_env"
            assert na.database_id == "env_db_id"


# ── agregar_entrada ───────────────────────────────────────────────────────────

def test_agregar_entrada_basic(automation, mock_notion_client):
    mock_notion_client.pages.create.return_value = {"id": "page-1", "url": "https://notion.so/page-1"}

    result = automation.agregar_entrada(titulo="Tarea 1")

    assert result["id"] == "page-1"
    call_kwargs = mock_notion_client.pages.create.call_args.kwargs
    parent = call_kwargs["parent"]
    props = call_kwargs["properties"]

    assert parent == {"database_id": "db_test_id"}
    assert props["Nombre"]["title"][0]["text"]["content"] == "Tarea 1"
    assert props["Materia"]["select"]["name"] == "Otra"  # default
    assert props["Estado"]["select"]["name"] == "Por hacer"  # default
    assert props["Prioridad"]["select"]["name"] == "Media"  # default


def test_agregar_entrada_with_all_fields(automation, mock_notion_client):
    mock_notion_client.pages.create.return_value = {"id": "page-2", "url": ""}

    automation.agregar_entrada(
        titulo="Proyecto Final",
        materia="Ingeniería de Software",
        tipo="Proyecto",
        estado="En progreso",
        prioridad="Alta",
        descripcion="Descripción del proyecto",
        fecha_limite="2026-06-30",
    )

    props = mock_notion_client.pages.create.call_args.kwargs["properties"]
    assert props["Materia"]["select"]["name"] == "Ingeniería de Software"
    assert props["Tipo"]["select"]["name"] == "Proyecto"
    assert props["Estado"]["select"]["name"] == "En progreso"
    assert props["Prioridad"]["select"]["name"] == "Alta"
    assert props["Descripción"]["rich_text"][0]["text"]["content"] == "Descripción del proyecto"
    assert props["Fecha Límite"]["date"]["start"] == "2026-06-30"


def test_agregar_entrada_invalid_materia_defaults(automation, mock_notion_client):
    mock_notion_client.pages.create.return_value = {"id": "p3"}

    automation.agregar_entrada(titulo="Test", materia="Materia Inexistente")

    props = mock_notion_client.pages.create.call_args.kwargs["properties"]
    assert props["Materia"]["select"]["name"] == "Otra"


def test_agregar_entrada_invalid_estado_defaults(automation, mock_notion_client):
    mock_notion_client.pages.create.return_value = {"id": "p4"}

    automation.agregar_entrada(titulo="Test", estado="Estado Invalido")

    props = mock_notion_client.pages.create.call_args.kwargs["properties"]
    assert props["Estado"]["select"]["name"] == "Por hacer"


def test_agregar_entrada_api_error_raises(automation, mock_notion_client):
    from notion_client.errors import APIResponseError

    response_mock = MagicMock()
    response_mock.status_code = 400
    response_mock.json.return_value = {"message": "bad request"}
    mock_notion_client.pages.create.side_effect = APIResponseError(
        response_mock, "bad request", 400
    )

    with pytest.raises(RuntimeError, match="Error al crear la entrada"):
        automation.agregar_entrada(titulo="Fail")


# ── listar_entradas ───────────────────────────────────────────────────────────

def test_listar_entradas_sin_filtro(automation, mock_notion_client):
    mock_notion_client.databases.query.return_value = {"results": [{"id": "e1"}, {"id": "e2"}]}

    results = automation.listar_entradas()

    assert len(results) == 2
    call_kwargs = mock_notion_client.databases.query.call_args.kwargs
    assert call_kwargs["database_id"] == "db_test_id"
    assert "filter" not in call_kwargs


def test_listar_entradas_con_filtro_materia(automation, mock_notion_client):
    mock_notion_client.databases.query.return_value = {"results": []}

    automation.listar_entradas(materia="Proyecto Integrador")

    call_kwargs = mock_notion_client.databases.query.call_args.kwargs
    assert call_kwargs["filter"]["property"] == "Materia"
    assert call_kwargs["filter"]["select"]["equals"] == "Proyecto Integrador"


def test_listar_entradas_con_multiples_filtros(automation, mock_notion_client):
    mock_notion_client.databases.query.return_value = {"results": []}

    automation.listar_entradas(materia="Proyecto Integrador", estado="En progreso")

    call_kwargs = mock_notion_client.databases.query.call_args.kwargs
    assert "and" in call_kwargs["filter"]
    assert len(call_kwargs["filter"]["and"]) == 2


# ── actualizar_estado ─────────────────────────────────────────────────────────

def test_actualizar_estado_valido(automation, mock_notion_client):
    mock_notion_client.pages.update.return_value = {"id": "page-1"}

    result = automation.actualizar_estado("page-1", "Completado")

    assert result["id"] == "page-1"
    mock_notion_client.pages.update.assert_called_once_with(
        page_id="page-1",
        properties={"Estado": {"select": {"name": "Completado"}}},
    )


def test_actualizar_estado_invalido_raises(automation, mock_notion_client):
    with pytest.raises(ValueError, match="Estado inválido"):
        automation.actualizar_estado("page-1", "Estado Raro")


# ── eliminar_entrada ──────────────────────────────────────────────────────────

def test_eliminar_entrada(automation, mock_notion_client):
    mock_notion_client.pages.update.return_value = {"id": "page-1", "archived": True}

    result = automation.eliminar_entrada("page-1")

    assert result["archived"] is True
    mock_notion_client.pages.update.assert_called_once_with(
        page_id="page-1", archived=True
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def test_obtener_titulo(automation):
    page = {"properties": {"Nombre": {"title": [{"text": {"content": "Mi Tarea"}}]}}}
    assert automation.obtener_titulo(page) == "Mi Tarea"


def test_obtener_titulo_sin_datos(automation):
    assert automation.obtener_titulo({}) == "(sin título)"


def test_obtener_propiedad_select(automation):
    page = {"properties": {"Estado": {"select": {"name": "Completado"}}}}
    assert automation.obtener_propiedad_select(page, "Estado") == "Completado"


def test_obtener_propiedad_select_faltante(automation):
    assert automation.obtener_propiedad_select({}, "Estado") == ""


# ── Constantes de dominio ─────────────────────────────────────────────────────

def test_materias_incluidas():
    assert "Ingeniería de Software" in MATERIAS_6TO
    assert "Proyecto Integrador" in MATERIAS_6TO
    assert "Bases de Datos Avanzadas" in MATERIAS_6TO


def test_tipos_incluidos():
    assert "Tarea" in TIPOS_ENTRADA
    assert "Examen" in TIPOS_ENTRADA
    assert "Proyecto" in TIPOS_ENTRADA


def test_estados_incluidos():
    assert "Por hacer" in ESTADOS
    assert "En progreso" in ESTADOS
    assert "Completado" in ESTADOS
    assert "Cancelado" in ESTADOS


def test_prioridades_incluidas():
    assert "Alta" in PRIORIDADES
    assert "Media" in PRIORIDADES
    assert "Baja" in PRIORIDADES

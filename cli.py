"""
cli.py
Interfaz de línea de comandos para automatizar Notion (Sexto Semestre de Software).
Soporta comandos directos y, opcionalmente, lenguaje natural mediante OpenAI.
"""

import json
import os
import sys

from dotenv import load_dotenv

from notion_automation import (
    ESTADOS,
    MATERIAS_6TO,
    PRIORIDADES,
    TIPOS_ENTRADA,
    NotionAutomation,
)

load_dotenv()

# ── Ayuda de OpenAI (opcional) ────────────────────────────────────────────────

def _parse_with_openai(user_input: str) -> dict | None:
    """
    Usa OpenAI para convertir texto libre en parámetros estructurados.
    Devuelve None si OPENAI_API_KEY no está configurado.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI  # noqa: PLC0415

        client = OpenAI(api_key=api_key)
        system_prompt = (
            "Eres un asistente que ayuda a organizar tareas universitarias en Notion. "
            "El usuario te pedirá agregar una entrada a una base de datos para el 6to semestre de Ingeniería de Software. "
            "Debes responder ÚNICAMENTE con un objeto JSON con las siguientes claves:\n"
            "  titulo (string, requerido)\n"
            f"  materia (una de: {json.dumps(MATERIAS_6TO, ensure_ascii=False)})\n"
            f"  tipo (una de: {json.dumps(TIPOS_ENTRADA, ensure_ascii=False)})\n"
            f"  estado (una de: {json.dumps(ESTADOS, ensure_ascii=False)})\n"
            f"  prioridad (una de: {json.dumps(PRIORIDADES, ensure_ascii=False)})\n"
            "  descripcion (string, opcional)\n"
            "  fecha_limite (formato YYYY-MM-DD, opcional)\n"
            "Si no puedes determinar un valor, usa el valor por defecto razonable."
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as exc:  # noqa: BLE001
        print(f"[Advertencia] No se pudo usar OpenAI: {exc}")
        return None


# ── Menú interactivo ──────────────────────────────────────────────────────────

def _elegir(opciones: list[str], etiqueta: str) -> str:
    """Presenta un menú numerado y retorna la opción elegida."""
    print(f"\n{etiqueta}:")
    for i, opcion in enumerate(opciones, 1):
        print(f"  {i}. {opcion}")
    while True:
        entrada = input("  Selecciona un número: ").strip()
        if entrada.isdigit() and 1 <= int(entrada) <= len(opciones):
            return opciones[int(entrada) - 1]
        print("  Opción inválida, intenta de nuevo.")


def cmd_agregar(notion: NotionAutomation, texto_libre: str = "") -> None:
    """Agrega una nueva entrada a la base de datos."""
    params: dict = {}

    if texto_libre:
        parsed = _parse_with_openai(texto_libre)
        if parsed:
            params = parsed
            print("\n[IA] Parámetros detectados:")
            for k, v in params.items():
                if v:
                    print(f"  {k}: {v}")

    # Solicitar los campos faltantes interactivamente
    if not params.get("titulo"):
        params["titulo"] = input("\nTítulo de la entrada: ").strip()
        if not params["titulo"]:
            print("El título es requerido.")
            return

    if not params.get("materia"):
        params["materia"] = _elegir(MATERIAS_6TO, "Materia")

    if not params.get("tipo"):
        params["tipo"] = _elegir(TIPOS_ENTRADA, "Tipo")

    if not params.get("estado"):
        params["estado"] = _elegir(ESTADOS, "Estado")

    if not params.get("prioridad"):
        params["prioridad"] = _elegir(PRIORIDADES, "Prioridad")

    if not params.get("descripcion"):
        desc = input("\nDescripción (opcional, Enter para omitir): ").strip()
        if desc:
            params["descripcion"] = desc

    if not params.get("fecha_limite"):
        fecha = input("Fecha límite (YYYY-MM-DD, Enter para omitir): ").strip()
        if fecha:
            params["fecha_limite"] = fecha

    print("\nCreando entrada en Notion…")
    page = notion.agregar_entrada(**params)
    print(f"✅ Entrada creada exitosamente: {page.get('url', '')}")


def cmd_listar(notion: NotionAutomation) -> None:
    """Lista las entradas de la base de datos con filtros opcionales."""
    print("\nFiltros opcionales (Enter para omitir):")

    materia_input = input("Materia: ").strip()
    estado_input = input("Estado: ").strip()
    tipo_input = input("Tipo: ").strip()

    materia = materia_input if materia_input in MATERIAS_6TO else None
    estado = estado_input if estado_input in ESTADOS else None
    tipo = tipo_input if tipo_input in TIPOS_ENTRADA else None

    entradas = notion.listar_entradas(materia=materia, estado=estado, tipo=tipo)

    if not entradas:
        print("No se encontraron entradas con los filtros dados.")
        return

    print(f"\n{'─' * 60}")
    for entrada in entradas:
        titulo = notion.obtener_titulo(entrada)
        mat = notion.obtener_propiedad_select(entrada, "Materia")
        est = notion.obtener_propiedad_select(entrada, "Estado")
        tip = notion.obtener_propiedad_select(entrada, "Tipo")
        print(f"  [{tip}] {titulo}")
        print(f"       Materia: {mat}  |  Estado: {est}")
        print(f"       ID: {entrada['id']}")
        print(f"{'─' * 60}")
    print(f"\nTotal: {len(entradas)} entrada(s)")


def cmd_actualizar_estado(notion: NotionAutomation) -> None:
    """Actualiza el estado de una entrada existente."""
    page_id = input("\nID de la página a actualizar: ").strip()
    if not page_id:
        print("ID requerido.")
        return

    nuevo_estado = _elegir(ESTADOS, "Nuevo estado")
    page = notion.actualizar_estado(page_id, nuevo_estado)
    print(f"✅ Estado actualizado: {page.get('url', '')}")


def cmd_eliminar(notion: NotionAutomation) -> None:
    """Archiva una entrada de la base de datos."""
    page_id = input("\nID de la página a archivar: ").strip()
    if not page_id:
        print("ID requerido.")
        return

    confirmacion = input(f"¿Archivar la entrada '{page_id}'? (s/N): ").strip().lower()
    if confirmacion != "s":
        print("Operación cancelada.")
        return

    notion.eliminar_entrada(page_id)
    print("✅ Entrada archivada exitosamente.")


# ── Punto de entrada ──────────────────────────────────────────────────────────

MENU = {
    "1": ("Agregar entrada", cmd_agregar),
    "2": ("Listar entradas", cmd_listar),
    "3": ("Actualizar estado", cmd_actualizar_estado),
    "4": ("Archivar entrada", cmd_eliminar),
    "5": ("Salir", None),
}


def main(argv: list[str] | None = None) -> None:
    """Punto de entrada principal del CLI."""
    argv = argv or sys.argv[1:]

    try:
        notion = NotionAutomation()
    except ValueError as exc:
        print(f"Error de configuración: {exc}")
        sys.exit(1)

    # Modo de lenguaje natural (pasa el texto como argumento)
    if argv:
        texto_libre = " ".join(argv)
        print(f"Procesando: «{texto_libre}»")
        cmd_agregar(notion, texto_libre)
        return

    # Modo interactivo
    print("=" * 60)
    print("  Nexus-IA — Automatización de Notion")
    print("  Sexto Semestre de Ingeniería de Software")
    print("=" * 60)

    while True:
        print("\n¿Qué deseas hacer?")
        for key, (label, _) in MENU.items():
            print(f"  {key}. {label}")

        opcion = input("\nSelecciona una opción: ").strip()

        if opcion not in MENU:
            print("Opción inválida.")
            continue

        label, fn = MENU[opcion]
        if fn is None:
            print("¡Hasta luego!")
            break

        try:
            if opcion == "1":
                texto = input(
                    "\nDescribe lo que quieres agregar "
                    "(o presiona Enter para modo manual): "
                ).strip()
                fn(notion, texto)
            else:
                fn(notion)
        except RuntimeError as exc:
            print(f"Error: {exc}")
        except KeyboardInterrupt:
            print("\nOperación cancelada.")


if __name__ == "__main__":
    main()

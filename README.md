# nexus-ia

Automatización de Notion para el **Sexto Semestre de Ingeniería de Software**.
Permite agregar, listar y actualizar entradas en una base de datos de Notion mediante
un CLI interactivo o lenguaje natural (con OpenAI opcional).

---

## Requisitos

- Python 3.12+
- Una cuenta de Notion con una integración creada en <https://www.notion.so/my-integrations>
- Una base de datos de Notion compartida con la integración (ver sección de configuración)

---

## Instalación

```bash
pip install -r requirements.txt
```

---

## Configuración

1. Copia el archivo de ejemplo y completa tus credenciales:

   ```bash
   cp .env.example .env
   ```

2. Edita `.env`:

   ```env
   NOTION_TOKEN=secret_xxxx          # Token de tu integración de Notion
   NOTION_DATABASE_ID=xxxx           # ID de tu base de datos de Notion
   OPENAI_API_KEY=sk-xxxx            # (Opcional) Para lenguaje natural
   ```

### ¿Cómo obtener el `NOTION_DATABASE_ID`?

Abre la base de datos en Notion en el navegador. La URL tiene la forma:

```
https://www.notion.so/<workspace>/<DATABASE_ID>?v=<view_id>
```

El `DATABASE_ID` es la cadena hexadecimal de 32 caracteres antes del `?v=`.

### Estructura de la base de datos de Notion

La base de datos debe tener las siguientes propiedades (columnas):

| Nombre       | Tipo     | Opciones                                                             |
|--------------|----------|----------------------------------------------------------------------|
| Nombre       | Título   | —                                                                    |
| Materia      | Select   | Ingeniería de Software, Bases de Datos Avanzadas, Redes y Comunicaciones, Arquitectura de Software, Seguridad Informática, Proyecto Integrador, Otra |
| Tipo         | Select   | Tarea, Examen, Proyecto, Apunte, Recurso, Actividad                  |
| Estado       | Select   | Por hacer, En progreso, Completado, Cancelado                        |
| Prioridad    | Select   | Alta, Media, Baja                                                    |
| Descripción  | Texto    | —                                                                    |
| Fecha Límite | Fecha    | —                                                                    |

---

## Uso

### Modo interactivo (menú)

```bash
python cli.py
```

### Modo lenguaje natural (requiere `OPENAI_API_KEY`)

Pasa tu solicitud directamente como argumento:

```bash
python cli.py "agrega la tarea de redes sobre TCP/IP para el viernes con prioridad alta"
```

### Uso como módulo Python

```python
from notion_automation import NotionAutomation

notion = NotionAutomation()

# Agregar entrada
notion.agregar_entrada(
    titulo="Examen parcial de Seguridad",
    materia="Seguridad Informática",
    tipo="Examen",
    estado="Por hacer",
    prioridad="Alta",
    fecha_limite="2026-04-10",
)

# Listar entradas pendientes
entradas = notion.listar_entradas(estado="Por hacer")
for e in entradas:
    print(notion.obtener_titulo(e))

# Actualizar estado
notion.actualizar_estado(page_id="<id>", nuevo_estado="Completado")

# Archivar entrada
notion.eliminar_entrada(page_id="<id>")
```

---

## Tests

```bash
python -m pytest tests/ -v
```

---

## Estructura del proyecto

```
nexus-ia/
├── notion_automation.py   # Módulo principal de integración con Notion
├── cli.py                 # Interfaz de línea de comandos
├── requirements.txt       # Dependencias Python
├── .env.example           # Plantilla de variables de entorno
├── tests/
│   └── test_notion_automation.py
└── README.md
```

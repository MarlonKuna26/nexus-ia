import requests
import dateparser
import calendar
import re
import os
from datetime import datetime, timedelta
from string import punctuation
from difflib import SequenceMatcher
from dotenv import load_dotenv

# --- CARGAR VARIABLES DE ENTORNO ---
load_dotenv()

# --- CONFIGURACIÓN SEGURA (desde variables de entorno) ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# Validación de configuración
if not NOTION_TOKEN or not DATABASE_ID:
    raise ValueError(
        "❌ ERROR: Falta NOTION_TOKEN o DATABASE_ID en .env\n"
        "Por favor crea un archivo .env en la raíz del proyecto con:\n"
        "NOTION_TOKEN=tu_token_aqui\n"
        "DATABASE_ID=tu_database_id_aqui"
    )

# --- STOPWORDS EN ESPAÑOL ---
STOPWORDS_ES = {
    'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se',
    'no', 'haber', 'por', 'con', 'su', 'para', 'es', 'o', 'como',
    'estar', 'tener', 'le', 'lo', 'todo', 'pero', 'más', 'hacer',
    'poder', 'decir', 'este', 'ir', 'otro', 'ese', 'esta', 'son',
    'los', 'las', 'del', 'al', 'desde', 'hasta', 'me', 'te', 'nos'
}

# --- DICCIONARIO MEJORADO CON VARIANTES ---
DICCIONARIO_MATERIAS_MEJORADO = {
    "web": {
        "nombre": "Aplicaciones Web y Móviles",
        "variantes": ["web", "móvil", "mobile", "app", "webapp", "aplicación", "frontend", "backend", "react", "angular"]
    },
    "bi": {
        "nombre": "Inteligencia de negocios",
        "variantes": ["bi", "negocios", "inteligencia", "analytics", "datos", "data", "tableau", "powerbi", "business"]
    },
    "realidad": {
        "nombre": "Realidad Nacional",
        "variantes": ["realidad", "nacional", "sociedad", "contexto"]
    },
    "distribuidas": {
        "nombre": "Aplicaciones distribuidas",
        "variantes": ["distribuidas", "distribuido", "microservicios", "cloud", "kubernetes", "docker"]
    },
    "gestión": {
        "nombre": "Gestión de prueba e implantación",
        "variantes": ["gestión", "gestion", "prueba", "qa", "testing", "implantación", "deployment"]
    },
    "inglés": {
        "nombre": "Inglés B1+",
        "variantes": ["inglés", "ingles", "english", "b1"]
    }
}

# --- FUNCIONES DE PROCESAMIENTO DE LENGUAJE ---

def normalizar_texto(texto):
    """Limpia puntuación, accentes, espacios múltiples"""
    # Remover puntuación
    texto = texto.translate(str.maketrans('', '', punctuation))
    # Normalizar espacios
    texto = re.sub(r'\s+', ' ', texto).strip()
    # Minúsculas
    return texto.lower()

def tokenizar(texto):
    """Divide texto en palabras individuales"""
    texto_limpio = normalizar_texto(texto)
    return texto_limpio.split()

def remover_stopwords(tokens):
    """Elimina palabras comunes sin valor semántico"""
    return [t for t in tokens if t not in STOPWORDS_ES]

def tiene_negacion(tokens, palabra, ventana=3):
    """Detecta si 'no' aparece cerca de la palabra"""
    negaciones = ['no', 'nunca', 'jamás', 'nada', 'ni']
    if palabra not in tokens:
        return False
    idx = tokens.index(palabra)
    inicio = max(0, idx - ventana)
    fin = min(len(tokens), idx + ventana)
    return any(tokens[i] in negaciones for i in range(inicio, fin))

def buscar_concepto_fuzzy(entrada, opciones, umbral=0.75):
    """Encuentra el concepto más similar incluso con typos o variaciones"""
    mejores = []
    entrada_norm = normalizar_texto(entrada)
    
    for opcion in opciones:
        opcion_norm = normalizar_texto(opcion)
        similitud = SequenceMatcher(None, entrada_norm, opcion_norm).ratio()
        if similitud >= umbral:
            mejores.append((opcion, similitud))
    
    if mejores:
        return max(mejores, key=lambda x: x[1])[0]
    return None

# --- FUNCIONES DE FECHA ---

def _clamp_day(year, month, day):
    last = calendar.monthrange(year, month)[1]
    return min(day, last)

def _safe_date(year, month, day):
    day = _clamp_day(year, month, day)
    return datetime(year, month, day)

def _obtener_proximo_dia_semana(nombre_dia, ahora, proxima_semana=False):
    """Obtiene la próxima ocurrencia de un día de la semana."""
    dias_es = {
        "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2,
        "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6
    }
    
    if nombre_dia not in dias_es:
        return None
    
    dia_objetivo = dias_es[nombre_dia]
    dia_actual = ahora.weekday()
    
    # Calcular días hasta el próximo día objetivo
    dias_adelante = (dia_objetivo - dia_actual) % 7
    
    if proxima_semana:
        # Fuerza semana siguiente (mínimo 7 días)
        if dias_adelante == 0:
            dias_adelante = 7
        else:
            dias_adelante += 7
    else:
        # "Este" = el más cercano (puede ser hoy o próximos 6 días)
        if dias_adelante == 0:
            dias_adelante = 0  # Hoy mismo
    
    return ahora + timedelta(days=dias_adelante)

def _pedir_confirmacion_fecha(texto_original, fecha_actual, ahora):
    dia = fecha_actual.day
    try:
        fecha_este = _safe_date(ahora.year, ahora.month, dia)
    except Exception:
        fecha_este = None
    
    next_month = ahora.month + 1
    next_year = ahora.year
    if next_month == 13:
        next_month = 1
        next_year += 1
    fecha_proximo = _safe_date(next_year, next_month, dia)

    fmt = lambda d: d.strftime("%Y-%m-%d") if d else "N/A"
    print(f"Confirmación necesaria para: '{texto_original}'")
    print(f"Opciones: 1) este mes -> {fmt(fecha_este)}   2) próximo mes -> {fmt(fecha_proximo)}")
    print("Responde: 'este' / 'próximo' / o escribe otra fecha en formato YYYY-MM-DD")
    while True:
        resp = input("Tu elección: ").strip().lower()
        if resp in ("este", "este mes"):
            if fecha_este and fecha_este.date() >= ahora.date():
                return fecha_este
            else:
                print("No es posible usar esa fecha. Elige otra opción.")
        elif resp in ("próximo", "proximo", "siguiente", "próximo mes"):
            return fecha_proximo
        else:
            try:
                fecha_usuario = datetime.strptime(resp, "%Y-%m-%d")
                return fecha_usuario
            except Exception:
                fecha_parse = dateparser.parse(resp, languages=['es'], settings={'RELATIVE_BASE': ahora})
                if fecha_parse:
                    return fecha_parse
                print("No entendí la respuesta. Responde 'este', 'próximo' o YYYY-MM-DD.")

def extraer_fechas_mejorado(texto):
    """Extrae fechas con múltiples patrones mejorados"""
    texto_min = texto.lower()
    
    patrones = [
        # "27 de febrero", "27 febrero"
        (r'(\d{1,2})\s*de\s+(\w+)', 'explicita'),
        # "en 2 semanas", "en 3 días"
        (r'en\s+(\d+)\s+(semanas?|días?|horas?|meses?)', 'relativa'),
        # "mañana", "hoy", "pasado mañana"
        (r'\b(mañana|hoy|pasado\s+mañana|ayer)\b', 'relativa'),
        # "próximo lunes", "siguiente martes"
        (r'(próximo|proximo|siguiente|este)\s+(lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', 'dia_semana'),
    ]
    
    for patrón, tipo in patrones:
        match = re.search(patrón, texto_min, re.IGNORECASE)
        if match:
            return match.groups(), tipo
    
    return None, None

def procesar_logica_negocio(texto):
    texto_min = texto.lower()
    ahora = datetime.now()
    
    # Tokenización y normalización
    tokens = tokenizar(texto)
    tokens_clean = remover_stopwords(tokens)
    
    # 1. MATERIAS - Con variantes mejoradas
    materia_final = ""
    for categoria, datos in DICCIONARIO_MATERIAS_MEJORADO.items():
        # Buscar cualquier variante en los tokens limpios
        if any(var in tokens_clean for var in datos["variantes"]):
            materia_final = datos["nombre"]
            break
    
    # Si no encontró, intenta fuzzy matching
    if not materia_final:
        todas_variantes = []
        for datos in DICCIONARIO_MATERIAS_MEJORADO.values():
            todas_variantes.extend(datos["variantes"])
        
        for token in tokens_clean:
            encontrado = buscar_concepto_fuzzy(token, todas_variantes, umbral=0.75)
            if encontrado:
                # Buscar la materia correspondiente
                for cat, datos in DICCIONARIO_MATERIAS_MEJORADO.items():
                    if encontrado in datos["variantes"]:
                        materia_final = datos["nombre"]
                        break
            if materia_final:
                break

    # 2. TIPOS - Con fuzzy matching para typos
    tipos_disponibles = ["examen", "proyecto", "deber", "entrega", "taller"]
    tipos_palabras_clave = {
        "examen": ["examen", "prueba", "test", "parcial", "final", "evaluación", "quiz", "exam"],
        "proyecto": ["proyecto", "trabajo", "investigación", "paper", "trabajo final"],
        "entrega": ["entrega", "foro", "submission", "entregar"],
        "taller": ["taller", "workshop", "práctica"]
    }
    
    tipo = "Deber"  # Default
    for tipo_nombre, palabras in tipos_palabras_clave.items():
        if any(p in tokens_clean for p in palabras):
            tipo = tipo_nombre.capitalize()
            break
    
    # Si no encontró, intenta fuzzy matching en tokens
    if tipo == "Deber":
        for token in tokens_clean:
            encontrado = buscar_concepto_fuzzy(token, tipos_disponibles, umbral=0.75)
            if encontrado:
                tipo = encontrado.capitalize()
                break

    # 3. PRIORIDAD - Mejorada con detección de negación
    prioridad = "Media"
    
    palabras_urgentes = ["urgente", "importante", "prioridad", "crítico", "critico", "urge", "asap"]
    palabras_bajas = ["suave", "bajo", "fácil", "facil", "simple", "fácilmente", "facilmente"]
    
    # Alta prioridad
    if any(p in tokens_clean for p in palabras_urgentes):
        if not tiene_negacion(tokens, "urgente") and not tiene_negacion(tokens, "importante"):
            prioridad = "Alta"
    
    # Baja prioridad (solo si no hay urgencia)
    if prioridad == "Media" and any(p in tokens_clean for p in palabras_bajas):
        prioridad = "Baja"

    # --- 4. LÓGICA DE FECHA - MEJORADA ---
    meses_es = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    dias_es = ["lunes", "martes", "miercoles", "miércoles", "jueves", "viernes", "sabado", "sábado", "domingo"]
    meses_pattern = "|".join(meses_es.keys())
    
    fecha_dt = None
    
    # PATRÓN 1: Intenta con los nuevos patrones mejorados
    grupos, tipo_fecha = extraer_fechas_mejorado(texto)
    if grupos and tipo_fecha == 'explicita':
        dia_num = int(grupos[0])
        mes_nombre = grupos[1]
        if mes_nombre in meses_es:
            mes_num = meses_es[mes_nombre]
            año = ahora.year
            if mes_num < ahora.month or (mes_num == ahora.month and dia_num < ahora.day):
                año += 1
            try:
                fecha_dt = _safe_date(año, mes_num, dia_num)
            except:
                fecha_dt = None
    
    # PATRÓN 2: Detectar "próximo/siguiente + día de semana"
    if not fecha_dt and any(kw in texto_min for kw in ["próximo", "proximo", "siguiente"]):
        for dia in dias_es:
            if dia in texto_min:
                fecha_dt = _obtener_proximo_dia_semana(dia, ahora, proxima_semana=True)
                break
    
    # PATRÓN 3: Detectar "este + día de semana"
    if not fecha_dt and any(kw in texto_min for kw in ["este", "este semana"]):
        for dia in dias_es:
            if dia in texto_min:
                fecha_dt = _obtener_proximo_dia_semana(dia, ahora, proxima_semana=False)
                break
    
    # PATRÓN 4: Fallback con dateparser
    if not fecha_dt:
        fecha_dt = dateparser.parse(
            texto_min, 
            languages=['es'], 
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': ahora,
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )
    
    if not fecha_dt:
        fecha_dt = ahora + timedelta(days=1)

    # Pedir confirmación si la fecha está en el pasado
    if fecha_dt.date() < ahora.date():
        fecha_dt = _pedir_confirmacion_fecha(texto, fecha_dt, ahora)

    return {
        "nombre": texto.capitalize(),
        "fecha": fecha_dt.strftime("%Y-%m-%d"),
        "tipo": tipo,
        "prioridad": prioridad,
        "materia": materia_final
    }

def enviar_a_notion(datos):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    propiedades = {
        "Nombre": { "title": [{"text": {"content": datos['nombre']}}] },
        "Fecha de Entrega": { "date": {"start": datos['fecha']} },
        "Prioridad": { "select": {"name": datos['prioridad']} },
        "Tipo": { "select": {"name": datos['tipo']} }
    }

    if datos['materia']:
        propiedades["Materia"] = { "select": {"name": datos['materia']} }

    payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": propiedades
    }
    
    return requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    print("--- NEXUS v4.2 (Semana Inteligente) ---")
    orden = input("Marlon, ¿qué tarea agendamos?: ")
    
    info = procesar_logica_negocio(orden)
    print(f"-> Interpretado: {info['nombre']} | Fecha: {info['fecha']} | {info['materia']}")
    
    res = enviar_a_notion(info)
    if res.status_code == 200:
        print("✅ ¡Éxito! Ya aparece en tu Notion.")
    else:
        print(f"❌ Error {res.status_code}: {res.text}")
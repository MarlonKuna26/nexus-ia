from nexus_local import procesar_logica_negocio

# Pruebas de casos de uso
pruebas = [
    ("Examen de Web mañana", "Alta web"),
    ("Proyecto de BI para el 27 de febrero", "Proyecto BI"),
    ("No es urgente pero debo entregar el deber de realidad nacional", "Baja realidad"),
    ("Taller de aplicaciones distribuidas próximo lunes", "Distribuidas"),
    ("Paper investigación inteligencia negocios - crítico!", "Alta"),
    ("Entregar trabajo foro fácil suave", "Baja"),
    ("examne de Bi", "Typo tolerance"),
]

print("=== PRUEBAS DEL SISTEMA MEJORADO ===\n")
for entrada, desc in pruebas:
    try:
        resultado = procesar_logica_negocio(entrada)
        print(f"📝 [{desc}]")
        print(f"   Entrada: {entrada}")
        print(f"   ✓ Tipo: {resultado['tipo']}")
        print(f"   ✓ Materia: {resultado['materia'] or '(no detectada)'}")
        print(f"   ✓ Prioridad: {resultado['prioridad']}")
        print(f"   ✓ Fecha: {resultado['fecha']}")
        print()
    except Exception as e:
        print(f"❌ Error en '{entrada}': {e}\n")
        import traceback
        traceback.print_exc()
        print()

print("\n=== PRUEBAS DE FUNCIONES AUXILIARES ===\n")

# Prueba de tokenización y stopwords
from nexus_local import tokenizar, remover_stopwords, tiene_negacion

texto = "No es urgente pero importante resolver este problema"
tokens = tokenizar(texto)
tokens_clean = remover_stopwords(tokens)

print(f"Texto: {texto}")
print(f"Tokens: {tokens}")
print(f"Tokens limpios (sin stopwords): {tokens_clean}")
print(f"¿Tiene negación 'urgente'?: {tiene_negacion(tokens, 'urgente')}")
print()

# Prueba de fuzzy matching
from nexus_local import buscar_concepto_fuzzy

test_opciones = ["examen", "proyecto", "deber", "entrega"]
typos = ["examne", "proyeto", "debre", "entreega"]

print("Fuzzy Matching (tolerancia a typos):")
for typo in typos:
    resultado = buscar_concepto_fuzzy(typo, test_opciones, umbral=0.75)
    print(f"   '{typo}' → '{resultado}'")

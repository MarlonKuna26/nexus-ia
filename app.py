from flask import Flask, request, jsonify
from flask_cors import CORS
import json
# Importamos tus funciones de nexus_local
from nexus_local import procesar_logica_negocio, enviar_a_notion

app = Flask(__name__)
CORS(app)

@app.route('/agendar', methods=['POST'])
def api_agendar():
    # Iniciamos con una respuesta de error por si algo falla en el camino
    try:
        # 1. Obtener datos de forma segura
        data = request.get_json(force=True, silent=True)
        
        if not data:
            return jsonify({"status": "error", "mensaje": "No se recibió un JSON válido"}), 400

        orden_usuario = data.get('orden')
        if not orden_usuario:
            return jsonify({"status": "error", "mensaje": "Falta el campo 'orden'"}), 400

        # 2. Procesar lógica (Fecha, Materia, etc.)
        print(f"Procesando: {orden_usuario}") # Esto saldrá en tu terminal
        info_tarea = procesar_logica_negocio(orden_usuario)
        
        # 3. Enviar a Notion
        respuesta_notion = enviar_a_notion(info_tarea)
        
        # 4. Retornar respuesta SIEMPRE
        if respuesta_notion.status_code == 200:
            return jsonify({
                "status": "success",
                "mensaje": "Tarea guardada",
                "detalle": info_tarea
            }), 200
        else:
            return jsonify({
                "status": "error", 
                "mensaje": "Error en Notion", 
                "notion_raw": respuesta_notion.text
            }), 500

    except Exception as e:
        # Este return es vital para que Flask no se quede "colgado" si el código falla
        print(f"Error interno: {str(e)}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500
@app.route('/')
def home():
    # Esto envía tu página web cuando entras a http://192.168.1.3:5000
    from flask import send_from_directory
    return send_from_directory('.', 'index.html')
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
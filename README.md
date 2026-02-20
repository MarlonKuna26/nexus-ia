# NEXUS - Automatización Inteligente de Tareas


### ¿Cómo funciona?

1. **`.env`** - Archivo LOCAL con tus credenciales reales (NO debe subirse a GitHub)
2. **`.env.example`** - Plantilla que DEBE subirse a GitHub (sin valores sensibles)
3. **`.gitignore`** - Configura Git para ignorar `.env` automáticamente

### 🚀 Instrucciones de Uso

#### Para ti (local):
```bash
# Ya está configurado automáticamente
# El archivo .env se carga al ejecutar nexus_local.py
python nexus_local.py
```

#### Para otros desarrolladores (después de clonar desde GitHub):
```bash
# 1. Clonar el repositorio
git clone <tu-repo-url>
cd Automatizacion

# 2. Copiar plantilla de configuración
cp .env.example .env

# 3. Editar .env con tus credenciales
notepad .env

# 4. Ejecutar
python nexus_local.py
```

### 📋 Instrucciones para GitHub

#### 1. Inicializar repositorio (si no lo has hecho):
```bash
git init
git add .
git commit -m "Initial commit: Automatización inteligente de tareas"
```

#### 2. Verificar que .env NO está staged:
```bash
git status
# Deberías ver que .env NO aparece en los cambios a estar
```

#### 3. Si .env ya fue commiteado accidentalmente:
```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
# IMPORTANTE: En GitHub, ir a Settings > Secrets y regenerar los tokens
```

#### 4. Cambiar tokens (RECOMENDADO después de que hayan sido expuestos):
```
En Notion:
1. Ve a https://www.notion.so/my-integrations
2. Elimina la integración anterior
3. Crea una nueva integración
4. Copia el nuevo token a .env
5. Actualiza DATABASE_ID si es necesario
```

### 📁 Estructura de Seguridad

```
Automatizacion/
├── .env                    ← TU configuración LOCAL (secretos reales) [NUNCA SUBIR]
├── .env.example            ← Plantilla pública (sin secretos) [SUBIR A GITHUB]
├── .gitignore              ← Indica a Git qué ignorar [SUBIR A GITHUB]
├── nexus_local.py          ← Código principal
├── test_mejoras.py         ← Pruebas
└── README.md               ← Este archivo
```

### 🔐 Checklist de Seguridad

Antes de hacer push a GitHub:

- [ ] `.env` está listado en `.gitignore`
- [ ] `git status` NO muestra `.env`
- [ ] `git log --name-only` NO contiene `.env`
- [ ] `.env.example` contiene la estructura pero sin valores reales
- [ ] Ningún token aparece en archivos `.py` (todos en `.env`)

### ✅ Verificación Final

```bash
# Verificar que .env no se va a subir
git status

# Verificar que .gitignore está correcto
cat .gitignore | grep ".env"

# Ver qué se subiría a GitHub
git ls-files | grep -E "\.env|token|secret"
# Debería estar VACÍO
```

### 📞 Soporte

Si por accidente subiste tokens a GitHub:
1. Regenera los tokens en Notion inmediatamente
2. Revisa el historial de commits: `git log --all --oneline`
3. Considera hacer un commit que elimine el archivo: `git rm --cached .env`

---

**Versión:** 4.2  
**Protección:** Variables de entorno con python-dotenv  
**Estado:** ✅ Seguro para subir a GitHub

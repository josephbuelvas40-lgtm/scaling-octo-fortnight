# 🚀 Guía de Despliegue - Render + GitHub

## 📁 Estructura Final del Proyecto

```
dashboard/
├── api/                     # Módulo API REST
│   ├── __init__.py         # Inicialización del paquete
│   ├── main.py            # API principal con FastAPI
│   ├── requirements.txt    # Dependencias de la API
│   └── README.md          # Documentación de la API
├── etl/                    # Módulo ETL
│   ├── __init__.py         # Inicialización del paquete
│   ├── etl_processor.py    # Procesador ETL
│   ├── requirements.txt    # Dependencias de ETL
│   └── README.md          # Documentación de ETL
├── dashboard.py            # Dashboard principal (Streamlit)
├── requirements.txt        # Dependencias principales
├── .env.example           # Ejemplo de configuración (NO .env)
├── .gitignore             # Archivos ignorados por Git
├── Procfile               # Configuración de despliegue
├── runtime.txt            # Versión de Python
└── README.md              # Documentación general
```

## 🔄 Pasos para Subir a GitHub

### 1. Inicializar Git (si no está inicializado)
```bash
git init
```

### 2. Agregar archivos
```bash
git add .
```

### 3. Commit inicial
```bash
git commit -m "Initial commit: Dashboard MySQL con ETL y API"
```

### 4. Crear repositorio en GitHub
- Ve a https://github.com
- Crea un nuevo repositorio llamado "dashboard-mysql"
- NO inicialices con README (ya tienes uno)

### 5. Conectar repositorio
```bash
git remote add origin https://github.com/tu-usuario/dashboard-mysql.git
git branch -M main
git push -u origin main
```

## 🚀 Pasos para Desplegar en Render

### 1. Crear cuenta en Render
- Ve a https://render.com
- Regístrate con tu cuenta de GitHub

### 2. Crear nuevo Web Service
- Dashboard → New → Web Service
- Conecta tu repositorio de GitHub
- Configura:

#### **Configuración del Web Service:**
- **Name**: dashboard-mysql
- **Branch**: main
- **Runtime**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0`

### 3. Configurar Variables de Entorno
En el panel de Render, agrega estas variables:

```
DB_HOST=tu-host-mysql
DB_USER=tu-usuario
DB_PASSWORD=tu-contraseña
DB_NAME=tu-base-de-datos
```

**Nota:** Para producción, necesitarás una base de datos MySQL en Render u otro servicio.

### 4. Desplegar
- Click en "Create Web Service"
- Render desplegará automáticamente tu aplicación
- Espera a que termine el despliegue (5-10 minutos)

## 🔧 Configuración de Base de Datos

### Opción 1: Render MySQL
- En Render, crea un servicio MySQL
- Copia las credenciales del servicio MySQL
- Agrégalas como variables de entorno en tu web service

### Opción 2: Base de datos externa
- Usa cualquier servicio MySQL externo
- Configura las variables de entorno con las credenciales

## ⚠️ Importante para el Despliegue

### Archivos que NO se suben a Git:
- `.env` (credenciales reales)
- `__pycache__/` (archivos temporales)
- `*.pyc` (archivos compilados)
- Archivos de logs y bases de datos locales

### Archivos de configuración necesarios:
- ✅ `.env.example` (plantilla de configuración)
- ✅ `Procfile` (comando de inicio)
- ✅ `runtime.txt` (versión de Python)
- ✅ `requirements.txt` (dependencias)
- ✅ `.gitignore` (archivos a ignorar)

## 🌐 URLs después del despliegue

### Dashboard (Streamlit):
- **Render**: `https://dashboard-mysql.onrender.com`
- **Local**: `http://localhost:8501`

### API (FastAPI):
- **Render**: `https://dashboard-mysql-api.onrender.com` (si despliegas separado)
- **Local**: `http://localhost:8000`

## 🐛 Solución de Problemas Comunes

### Error de conexión a MySQL
- Verifica que las variables de entorno estén configuradas en Render
- Asegúrate de que la base de datos sea accesible desde Render
- Revisa las credenciales en el panel de Render

### Error de dependencias
- Verifica que `requirements.txt` tenga las versiones correctas
- Asegúrate de que Python sea la versión correcta (3.11)

### Error de timeout
- El despliegue puede tardar varios minutos
- Revisa los logs en el panel de Render

## 📊 Verificación del Despliegue

### 1. Ver logs en Render
- Dashboard → Web Service → Logs
- Busca errores o advertencias

### 2. Ver estado del servicio
- Dashboard → Web Service → Status
- Debe mostrar "Live" cuando esté funcionando

### 3. Probar la aplicación
- Abre la URL proporcionada por Render
- Verifica que el dashboard cargue correctamente
- Prueba la conexión a la base de datos

## 🔒 Seguridad en Producción

- Nunca subas `.env` con credenciales reales
- Usa variables de entorno en Render
- Considera usar SSL/TLS para conexiones de base de datos
- Usa contraseñas fuertes para MySQL
- Implementa autenticación si es necesario

## 📞 Soporte

Para problemas específicos de despliegue:
- Documentación de Render: https://render.com/docs
- Documentación de Streamlit: https://docs.streamlit.io
- Comunidad de Render: https://community.render.com
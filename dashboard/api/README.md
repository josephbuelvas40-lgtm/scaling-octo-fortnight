# 🚀 API REST Dashboard MySQL

API REST completa para análisis de datos, procesamiento ETL y gestión de base de datos MySQL construida con FastAPI.

## 📁 Estructura del Módulo

```
api/
├── __init__.py           # Inicialización del paquete
├── main.py              # API principal con FastAPI
└── README.md            # Este archivo
```

## 🚀 Características

### 🔗 Endpoints de Conexión
- **POST /api/test-connection**: Prueba conexión a MySQL
- **GET /health**: Verificación de salud de la API

### 📊 Endpoints de Tablas
- **POST /api/tables**: Obtiene todas las tablas de la base de datos
- **POST /api/table/{table_name}**: Obtiene detalles de una tabla específica
- **POST /api/table/{table_name}/data**: Obtiene datos de una tabla con límite

### 📈 Endpoints de Análisis
- **POST /api/analyze/{table_name}**: Analiza una tabla con estadísticas detalladas
- **POST /api/quality-report/{table_name}**: Genera reporte de calidad de datos

### 🔍 Endpoints de Búsqueda
- **POST /api/search**: Búsqueda avanzada en tablas

### 🔄 Endpoints ETL
- **POST /api/etl**: Ejecuta pipeline ETL completo
- **POST /api/etl/extract**: Solo extracción de datos
- **POST /api/etl/transform**: Solo transformación de datos

### 📁 Endpoints de Archivos
- **POST /api/upload/{file_type}**: Carga archivos para procesamiento ETL
- **GET /api/export/{file_type}**: Exporta datos de ejemplo

### 📊 Endpoints de Estadísticas
- **GET /api/stats**: Estadísticas de la API

## 🏃‍♂️ Instalación y Ejecución

### Instalar dependencias
```bash
pip install fastapi uvicorn mysql-connector-python pandas openpyxl python-dotenv
```

### Ejecutar la API
```bash
# Desde el directorio principal
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Acceder a documentación
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📚 Ejemplos de Uso

### Probar conexión
```bash
curl -X POST "http://localhost:8000/api/test-connection" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "sistema_salud"
  }'
```

### Obtener tablas
```bash
curl -X POST "http://localhost:8000/api/tables" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "sistema_salud"
  }'
```

### Analizar tabla
```bash
curl -X POST "http://localhost:8000/api/analyze/pacientes" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "sistema_salud"
  }'
```

### Ejecutar ETL
```bash
curl -X POST "http://localhost:8000/api/etl" \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {
      "host": "localhost",
      "user": "root",
      "password": "",
      "database": "sistema_salud"
    },
    "extract": {
      "source_type": "mysql",
      "table_name": "pacientes"
    },
    "transformations": [
      {
        "type": "clean_nulls",
        "strategy": "drop"
      }
    ],
    "load": {
      "destination_type": "csv",
      "filename": "exported_data.csv"
    }
  }'
```

## 🔧 Modelos de Datos

### ConnectionConfig
```json
{
  "host": "localhost",
  "user": "root", 
  "password": "",
  "database": "sistema_salud"
}
```

### ExtractConfig
```json
{
  "source_type": "mysql",
  "table_name": "nombre_tabla",
  "query": "SELECT * FROM nombre_tabla WHERE condicion"
}
```

### TransformConfig
```json
{
  "type": "clean_nulls",
  "strategy": "drop"
}
```

### LoadConfig
```json
{
  "destination_type": "csv",
  "filename": "exported_data.csv"
}
```

## 🌐 CORS

La API está configurada para aceptar requests desde cualquier origen (CORS habilitado).

## 🔒 Seguridad

- Validación de datos con Pydantic
- Manejo de errores con HTTPException
- Sanitización de consultas SQL
- Gestión segura de credenciales

## 📊 Integración con Dashboard

Esta API se integra directamente con el dashboard principal:
- Proporciona endpoints para todas las funcionalidades del dashboard
- Permite acceso programático a análisis de datos
- Facilita integración con aplicaciones externas

## 🚀 Producción

Para despliegue en producción:

```bash
# Ejecutar con gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# O con uvicorn directamente
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📝 Notas

- La API requiere archivo `.env` con configuración de base de datos
- Los endpoints ETL requieren el módulo `etl` instalado
- Los archivos subidos se procesan en memoria por seguridad
- Los límites de datos pueden ajustarse según necesidad

## 🔗 Documentación Interactiva

Accede a la documentación interactiva Swagger UI en:
http://localhost:8000/docs
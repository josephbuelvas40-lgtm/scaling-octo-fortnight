# 🔄 Módulo ETL (Extract, Transform, Load)

Sistema completo de procesamiento de datos para extracción, transformación y carga de información.

## 📁 Estructura del Módulo

```
etl/
├── __init__.py           # Inicialización del paquete
├── etl_processor.py      # Clases y funciones principales ETL
└── README.md            # Este archivo
```

## 🚀 Funcionalidades

### 📥 EXTRACT (Extracción)
- **MySQL**: Extracción desde bases de datos MySQL con consultas SQL personalizadas
- **CSV**: Importación de archivos CSV
- **Excel**: Importación de archivos Excel (xlsx, xls) con selección de hojas
- **JSON**: Importación de archivos JSON

### 🔄 TRANSFORM (Transformación)
- **Limpieza de datos**: Eliminación de nulos, relleno con media/cero
- **Eliminación de duplicados**: Detección y eliminación de registros duplicados
- **Conversión de tipos**: Conversión a numérico, datetime, string
- **Filtrado**: Filtros por igualdad, comparación, contenido
- **Agregación**: Agrupación y funciones de agregación (sum, mean, count, min, max)
- **Modificación de columnas**: Renombrado, adición de columnas
- **Estandarización de texto**: lowercase, uppercase, title, strip
- **Normalización numérica**: Min-Max, Z-Score

### 📤 LOAD (Carga)
- **MySQL**: Carga en tablas MySQL (append, replace, fail)
- **CSV**: Exportación a archivos CSV
- **Excel**: Exportación a archivos Excel
- **JSON**: Exportación a archivos JSON

## 💻 Uso Básico

```python
from etl import ETLProcessor

# Crear instancia del procesador
etl = ETLProcessor()

# Configuración de extracción
extract_config = {
    'source_type': 'mysql',
    'table_name': 'mi_tabla',
    'query': 'SELECT * FROM mi_tabla WHERE fecha > "2024-01-01"'
}

# Transformaciones
transformations = [
    {'type': 'clean_nulls', 'strategy': 'drop'},
    {'type': 'remove_duplicates'},
    {'type': 'convert_types', 'column': 'edad', 'target_type': 'numeric'}
]

# Configuración de carga
load_config = {
    'destination_type': 'csv',
    'filename': 'datos_procesados.csv'
}

# Ejecutar pipeline
result_df, log = etl.run_pipeline(connection, extract_config, transformations, load_config)

# Ver log
for phase, message in log:
    print(f"{phase}: {message}")
```

## 📊 Funciones Auxiliares

### `export_data(df, format='csv')`
Exporta datos a diferentes formatos (CSV, Excel)

### `get_data_quality_report(df)`
Genera reporte de calidad de datos (nulos, duplicados, tipos, memoria)

### `suggest_transformations(df)`
Sugiere transformaciones basadas en análisis automático de datos

## 🔧 Configuración

### Extracción MySQL
```python
{
    'source_type': 'mysql',
    'table_name': 'nombre_tabla',
    'query': 'SELECT * FROM nombre_tabla WHERE condicion'  # opcional
}
```

### Extracción Archivos
```python
{
    'source_type': 'csv',  # o 'excel', 'json'
    'file': archivo_cargado,
    'sheet_name': '0'  # solo para Excel
}
```

### Transformaciones
```python
[
    {
        'type': 'clean_nulls',
        'strategy': 'drop'  # o 'fill_mean', 'fill_zero'
    },
    {
        'type': 'filter',
        'column': 'edad',
        'condition': 'greater_than',
        'value': 18
    },
    {
        'type': 'aggregate',
        'group_by': 'categoria',
        'agg_func': 'sum'
    }
]
```

### Carga
```python
{
    'destination_type': 'mysql',  # o 'csv', 'excel', 'json'
    'table_name': 'tabla_destino',  # para MySQL
    'if_exists': 'append',  # para MySQL
    'filename': 'salida.csv'  # para archivos
}
```

## 📈 Características Avanzadas

- **Log automático**: Registro detallado de cada fase del proceso
- **Validación de datos**: Detección de errores en cada etapa
- **Reportes de calidad**: Análisis automático de calidad de datos
- **Sugerencias inteligentes**: Recomendaciones de transformaciones
- **Manejo de errores**: Gestión robusta de excepciones

## 🔒 Seguridad

- Validación de tipos de datos
- Sanitización de consultas SQL
- Manejo seguro de archivos
- Gestión de memoria para datasets grandes

## 📞 Integración con Dashboard

Este módulo se integra directamente con el dashboard principal:
- Accesible desde la sección "Procesamiento ETL"
- Interfaz visual para configurar pipelines
- Visualización de resultados en tiempo real
- Exportación de resultados procesados
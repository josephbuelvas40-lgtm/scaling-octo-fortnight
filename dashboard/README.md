# 📊 Dashboard MySQL con Python

## Requisitos
- Python 3.8 o superior
- MySQL Server instalado y funcionando
- Base de datos con datos para analizar

## Instalación

1. Crear un entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar la conexión a MySQL:
```bash
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_NAME=tu_base_de_datos
```

## Ejecución

```bash
streamlit run dashboard.py
```

El dashboard se abrirá en http://localhost:8501
import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv
import io
import json
import numpy as np

load_dotenv()

st.set_page_config(
    page_title="Dashboard de Joseph MySQL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de tema
def apply_theme():
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
        .stApp {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# Navegación principal
def main_navigation():
    if 'page' not in st.session_state:
        st.session_state.page = 'inicio'
    
    st.sidebar.title("📊 Dashboard de Joseph")
    st.sidebar.markdown("---")
    
    pages = {
        '🏠 Inicio': 'inicio',
        '📊 Análisis de Datos': 'analisis',
        '📈 Visualizaciones': 'visualizaciones',
        '🔍 Búsqueda Avanzada': 'busqueda',
        '� Procesamiento ETL': 'etl',
        '�📝 Gestión de Datos': 'gestion',
        '⚙️ Configuración': 'configuracion'
    }
    
    selected_page = st.sidebar.radio("Navegación", list(pages.keys()))
    st.session_state.page = pages[selected_page]
    
    # Botón de cambio de tema
    if st.sidebar.button(f"🌙 Cambiar a {'Claro' if st.session_state.theme == 'dark' else 'Oscuro'}"):
        st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
        st.rerun()
    
    st.sidebar.markdown("---")
    
    return st.session_state.page

def create_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'sistema_salud')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error al conectar a MySQL: {e}")
        return None

def get_tables(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        return tables
    except Error as e:
        st.error(f"Error al obtener tablas: {e}")
        return []

def get_table_data(connection, table_name, limit=1000):
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        st.error(f"Error al obtener datos de {table_name}: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al obtener datos de {table_name}: {e}")
        return pd.DataFrame()

def get_table_info(connection, table_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        return columns
    except Error as e:
        st.error(f"Error al obtener información de columnas: {e}")
        return []

def get_statistics(connection, table_name):
    try:
        df = get_table_data(connection, table_name, limit=10000)
        if df.empty:
            return None
        
        stats = {
            'total_registros': len(df),
            'total_columnas': len(df.columns),
            'columnas': list(df.columns),
            'tipos_datos': df.dtypes.astype(str).to_dict(),
            'memoria_usada': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
        }
        return stats
    except Exception as e:
        st.error(f"Error al calcular estadísticas: {e}")
        return None

def generate_charts(df, table_name):
    charts = []
    
    for column in df.columns:
        unique_values = df[column].nunique()
        
        # Gráficos para datos categóricos
        if df[column].dtype == 'object' and unique_values > 1:
            value_counts_df = df[column].value_counts().reset_index()
            value_counts_df.columns = [column, 'count']
            
            # Gráfico de barras para cualquier cantidad de valores únicos razonable
            if unique_values <= 50:
                fig = px.bar(
                    value_counts_df,
                    x=column,
                    y='count',
                    title=f'Distribución de {column}',
                    labels={column: column, 'count': 'Conteo'}
                )
                charts.append(('bar', fig))
            
            # Gráfico de pastel solo para pocas categorías
            if unique_values <= 10:
                fig = px.pie(
                    value_counts_df,
                    values='count',
                    names=column,
                    title=f'Distribución de {column}'
                )
                charts.append(('pie', fig))
        
        # Gráficos para datos numéricos
        elif df[column].dtype in ['int64', 'float64', 'int32', 'float32']:
            fig = px.histogram(
                df,
                x=column,
                title=f'Distribución de {column}',
                nbins=30
            )
            charts.append(('histogram', fig))
    
    return charts

def insert_record(connection, table_name, data):
    try:
        cursor = connection.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        connection.commit()
        return True, "Registro insertado exitosamente"
    except Error as e:
        return False, f"Error al insertar registro: {e}"

def get_foreign_key_options(connection, table_name, column_name):
    try:
        cursor = connection.cursor()
        
        cursor.execute(f"""
            SELECT REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{table_name}'
            AND COLUMN_NAME = '{column_name}'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        
        fk_info = cursor.fetchone()
        
        if fk_info:
            ref_table = fk_info[0]
            ref_column = fk_info[1]
            
            cursor.execute(f"SELECT {ref_column}, * FROM {ref_table}")
            ref_data = cursor.fetchall()
            
            if ref_data:
                options = [(row[0], row) for row in ref_data]
                return options, ref_table, ref_column
        
        return None, None, None
    except Error as e:
        return None, None, None

def get_display_value(row, ref_column):
    if len(row) > 1:
        return f"{row[0]} - {row[1]}"
    return str(row[0])

def get_insert_form(connection, table_name, table_info):
    form_data = {}
    
    for col in table_info:
        col_name = col[0]
        col_type = col[1]
        is_null = col[2] == 'YES'
        
        if col_name.lower() == 'id':
            continue
        
        fk_options, ref_table, ref_column = get_foreign_key_options(connection, table_name, col_name)
        
        if fk_options:
            label = f"{col_name} ({col_type}) - Referencia: {ref_table}"
            if is_null:
                options_dict = {get_display_value(opt[1], ref_column): opt[0] for opt in fk_options}
                options_dict["-- Seleccionar --"] = None
                selected_display = st.selectbox(label, list(options_dict.keys()), key=f"insert_{col_name}")
                value = options_dict[selected_display]
            else:
                options_dict = {get_display_value(opt[1], ref_column): opt[0] for opt in fk_options}
                selected_display = st.selectbox(f"{label} *", list(options_dict.keys()), key=f"insert_{col_name}")
                value = options_dict[selected_display]
        elif 'int' in col_type.lower():
            if is_null:
                value = st.number_input(f"{col_name} ({col_type})", key=f"insert_{col_name}", value=0, format="%d")
            else:
                value = st.number_input(f"{col_name} ({col_type}) *", key=f"insert_{col_name}", value=0, format="%d")
        elif 'varchar' in col_type.lower() or 'text' in col_type.lower() or 'char' in col_type.lower():
            if is_null:
                value = st.text_input(f"{col_name} ({col_type})", key=f"insert_{col_name}")
            else:
                value = st.text_input(f"{col_name} ({col_type}) *", key=f"insert_{col_name}")
        elif 'date' in col_type.lower():
            if is_null:
                value = st.date_input(f"{col_name} ({col_type})", key=f"insert_{col_name}")
            else:
                value = st.date_input(f"{col_name} ({col_type}) *", key=f"insert_{col_name}")
        elif 'datetime' in col_type.lower() or 'timestamp' in col_type.lower():
            if is_null:
                value = st.datetime_input(f"{col_name} ({col_type})", key=f"insert_{col_name}")
            else:
                value = st.datetime_input(f"{col_name} ({col_type}) *", key=f"insert_{col_name}")
        elif 'decimal' in col_type.lower() or 'float' in col_type.lower() or 'double' in col_type.lower():
            if is_null:
                value = st.number_input(f"{col_name} ({col_type})", key=f"insert_{col_name}", value=0.0, format="%f")
            else:
                value = st.number_input(f"{col_name} ({col_type}) *", key=f"insert_{col_name}", value=0.0, format="%f")
        elif 'boolean' in col_type.lower():
            if is_null:
                value = st.checkbox(f"{col_name} ({col_type})", key=f"insert_{col_name}")
            else:
                value = st.checkbox(f"{col_name} ({col_type}) *", key=f"insert_{col_name}")
        else:
            if is_null:
                value = st.text_input(f"{col_name} ({col_type})", key=f"insert_{col_name}")
            else:
                value = st.text_input(f"{col_name} ({col_type}) *", key=f"insert_{col_name}")
        
        if value == '' or value is None:
            if not is_null:
                form_data[col_name] = None
            else:
                form_data[col_name] = None
        else:
            form_data[col_name] = value
    
    return form_data

# Funciones de exportación
def export_data(df, format='csv'):
    if format == 'csv':
        return df.to_csv(index=False).encode('utf-8')
    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

# Funciones de búsqueda avanzada
def advanced_search(connection, table_name, search_term, search_columns=None):
    try:
        if search_columns is None:
            # Obtener todas las columnas de texto
            col_info = get_table_info(connection, table_name)
            search_columns = [col[0] for col in col_info if 'text' in col[1].lower() or 'char' in col[1].lower() or 'varchar' in col[1].lower()]
        
        if not search_columns:
            return pd.DataFrame()
        
        conditions = []
        for col in search_columns:
            conditions.append(f"{col} LIKE '%{search_term}%'")
        
        query = f"SELECT * FROM {table_name} WHERE {' OR '.join(conditions)}"
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        st.error(f"Error en búsqueda: {e}")
        return pd.DataFrame()

# Funciones de paginación
def paginate_data(df, page_size=10):
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 1
    
    total_pages = (len(df) // page_size) + (1 if len(df) % page_size > 0 else 0)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀ Anterior", disabled=st.session_state.page_num == 1):
            st.session_state.page_num -= 1
            st.rerun()
    
    with col2:
        st.write(f"Página {st.session_state.page_num} de {total_pages}")
    
    with col3:
        if st.button("Siguiente ▶", disabled=st.session_state.page_num == total_pages):
            st.session_state.page_num += 1
            st.rerun()
    
    start_idx = (st.session_state.page_num - 1) * page_size
    end_idx = start_idx + page_size
    
    return df.iloc[start_idx:end_idx]

# ===== FUNCIONES ETL (Extract, Transform, Load) =====

# EXTRACT - Extracción de datos
def extract_data(connection, source_type, config):
    try:
        if source_type == 'mysql':
            table_name = config.get('table_name')
            query = config.get('query', f"SELECT * FROM {table_name}")
            df = pd.read_sql(query, connection)
            return df, f"Extraídos {len(df)} registros de MySQL"
        
        elif source_type == 'csv':
            file = config.get('file')
            if file:
                df = pd.read_csv(file)
                return df, f"Extraídos {len(df)} registros de CSV"
        
        elif source_type == 'excel':
            file = config.get('file')
            sheet_name = config.get('sheet_name', 0)
            if file:
                df = pd.read_excel(file, sheet_name=sheet_name)
                return df, f"Extraídos {len(df)} registros de Excel"
        
        elif source_type == 'json':
            file = config.get('file')
            if file:
                df = pd.read_json(file)
                return df, f"Extraídos {len(df)} registros de JSON"
        
        return pd.DataFrame(), "No se pudo extraer datos"
    
    except Exception as e:
        return pd.DataFrame(), f"Error en extracción: {e}"

# TRANSFORM - Transformación de datos
def transform_data(df, transformations):
    try:
        transformed_df = df.copy()
        transformations_applied = []
        
        for transform in transformations:
            transform_type = transform.get('type')
            
            if transform_type == 'clean_nulls':
                strategy = transform.get('strategy', 'drop')
                if strategy == 'drop':
                    transformed_df = transformed_df.dropna()
                    transformations_applied.append("Eliminados valores nulos")
                elif strategy == 'fill_mean':
                    numeric_cols = transformed_df.select_dtypes(include=[np.number]).columns
                    transformed_df[numeric_cols] = transformed_df[numeric_cols].fillna(transformed_df[numeric_cols].mean())
                    transformations_applied.append("Rellenados nulos con media")
                elif strategy == 'fill_zero':
                    transformed_df = transformed_df.fillna(0)
                    transformations_applied.append("Rellenados nulos con cero")
            
            elif transform_type == 'remove_duplicates':
                transformed_df = transformed_df.drop_duplicates()
                transformations_applied.append("Eliminados duplicados")
            
            elif transform_type == 'convert_types':
                column = transform.get('column')
                target_type = transform.get('target_type')
                if column in transformed_df.columns:
                    try:
                        if target_type == 'numeric':
                            transformed_df[column] = pd.to_numeric(transformed_df[column], errors='coerce')
                        elif target_type == 'datetime':
                            transformed_df[column] = pd.to_datetime(transformed_df[column], errors='coerce')
                        elif target_type == 'string':
                            transformed_df[column] = transformed_df[column].astype(str)
                        transformations_applied.append(f"Convertida columna {column} a {target_type}")
                    except Exception as e:
                        transformations_applied.append(f"Error convirtiendo {column}: {e}")
            
            elif transform_type == 'filter':
                column = transform.get('column')
                condition = transform.get('condition')
                value = transform.get('value')
                
                if column in transformed_df.columns:
                    if condition == 'equals':
                        transformed_df = transformed_df[transformed_df[column] == value]
                    elif condition == 'not_equals':
                        transformed_df = transformed_df[transformed_df[column] != value]
                    elif condition == 'greater_than':
                        transformed_df = transformed_df[transformed_df[column] > value]
                    elif condition == 'less_than':
                        transformed_df = transformed_df[transformed_df[column] < value]
                    elif condition == 'contains':
                        transformed_df = transformed_df[transformed_df[column].astype(str).str.contains(str(value), case=False, na=False)]
                    
                    transformations_applied.append(f"Filtrado por {column} {condition} {value}")
            
            elif transform_type == 'aggregate':
                group_by = transform.get('group_by')
                agg_func = transform.get('agg_func', 'sum')
                numeric_cols = transformed_df.select_dtypes(include=[np.number]).columns
                
                if group_by in transformed_df.columns and len(numeric_cols) > 0:
                    agg_dict = {col: agg_func for col in numeric_cols if col != group_by}
                    transformed_df = transformed_df.groupby(group_by).agg(agg_dict).reset_index()
                    transformations_applied.append(f"Agregado por {group_by} usando {agg_func}")
            
            elif transform_type == 'rename_columns':
                mapping = transform.get('mapping', {})
                transformed_df = transformed_df.rename(columns=mapping)
                transformations_applied.append("Columnas renombradas")
            
            elif transform_type == 'add_column':
                column_name = transform.get('column_name')
                expression = transform.get('expression')
                
                if expression == 'row_number':
                    transformed_df[column_name] = range(1, len(transformed_df) + 1)
                elif expression == 'timestamp':
                    transformed_df[column_name] = datetime.now()
                elif expression == 'year':
                    if 'fecha' in transformed_df.columns or 'date' in transformed_df.columns:
                        date_col = 'fecha' if 'fecha' in transformed_df.columns else 'date'
                        transformed_df[column_name] = pd.to_datetime(transformed_df[date_col]).dt.year
                
                transformations_applied.append(f"Agregada columna {column_name}")
        
        return transformed_df, transformations_applied
    
    except Exception as e:
        return df, [f"Error en transformación: {e}"]

# LOAD - Carga de datos
def load_data(df, destination_type, config, connection=None):
    try:
        if destination_type == 'mysql':
            table_name = config.get('table_name')
            if_exists = config.get('if_exists', 'append')
            
            if connection:
                df.to_sql(table_name, connection, if_exists=if_exists, index=False)
                return f"Cargados {len(df)} registros en tabla MySQL '{table_name}'"
            else:
                return "Error: No hay conexión a MySQL"
        
        elif destination_type == 'csv':
            filename = config.get('filename', 'exported_data.csv')
            df.to_csv(filename, index=False)
            return f"Guardados {len(df)} registros en '{filename}'"
        
        elif destination_type == 'excel':
            filename = config.get('filename', 'exported_data.xlsx')
            df.to_excel(filename, index=False)
            return f"Guardados {len(df)} registros en '{filename}'"
        
        elif destination_type == 'json':
            filename = config.get('filename', 'exported_data.json')
            df.to_json(filename, orient='records')
            return f"Guardados {len(df)} registros en '{filename}'"
        
        return "Tipo de destino no soportado"
    
    except Exception as e:
        return f"Error en carga: {e}"

# Función para ejecutar pipeline ETL completo
def run_etl_pipeline(connection, extract_config, transformations, load_config):
    etl_log = []
    
    # EXTRACT
    st.info("🔄 Fase 1: EXTRACCIÓN de datos...")
    extracted_df, extract_msg = extract_data(connection, extract_config['source_type'], extract_config)
    etl_log.append(("EXTRACT", extract_msg))
    
    if extracted_df.empty:
        return pd.DataFrame(), etl_log
    
    st.success(f"✅ {extract_msg}")
    st.dataframe(extracted_df.head(5), use_container_width=True)
    
    # TRANSFORM
    if transformations:
        st.info("🔄 Fase 2: TRANSFORMACIÓN de datos...")
        transformed_df, transform_msgs = transform_data(extracted_df, transformations)
        for msg in transform_msgs:
            etl_log.append(("TRANSFORM", msg))
            st.info(f"📝 {msg}")
        
        st.success(f"✅ Transformación completada. Registros finales: {len(transformed_df)}")
        st.dataframe(transformed_df.head(5), use_container_width=True)
    else:
        transformed_df = extracted_df
        etl_log.append(("TRANSFORM", "Sin transformaciones"))
    
    # LOAD
    st.info("🔄 Fase 3: CARGA de datos...")
    load_msg = load_data(transformed_df, load_config['destination_type'], load_config, connection)
    etl_log.append(("LOAD", load_msg))
    st.success(f"✅ {load_msg}")
    
    return transformed_df, etl_log

# Página de inicio
def page_inicio(connection):
    st.title("🏠 Panel de Control")
    st.markdown("---")
    
    tables = get_tables(connection)
    
    # KPIs generales
    col1, col2, col3, col4 = st.columns(4)
    
    total_tables = len(tables)
    total_records = 0
    total_memory = 0
    
    for table in tables:
        stats = get_statistics(connection, table)
        if stats:
            total_records += stats['total_registros']
            total_memory += float(stats['memoria_usada'].split()[0])
    
    col1.metric("Total Tablas", total_tables)
    col2.metric("Total Registros", total_records)
    col3.metric("Memoria Total", f"{total_memory:.2f} KB")
    col4.metric("Base de Datos", os.getenv('DB_NAME', 'sistema_salud'))
    
    st.markdown("---")
    
    # Resumen de tablas
    st.subheader("📊 Resumen de Tablas")
    
    table_summary = []
    for table in tables:
        stats = get_statistics(connection, table)
        if stats:
            table_summary.append({
                'Tabla': table,
                'Registros': stats['total_registros'],
                'Columnas': stats['total_columnas'],
                'Memoria': stats['memoria_usada']
            })
    
    if table_summary:
        summary_df = pd.DataFrame(table_summary)
        st.dataframe(summary_df, use_container_width=True)
    
    st.markdown("---")
    
    # Información del sistema
    st.subheader("💻 Información del Sistema")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Estado de conexión:** ✅ Conectado
        **Host:** {os.getenv('DB_HOST', 'localhost')}
        **Usuario:** {os.getenv('DB_USER', 'root')}
        **Base de datos:** {os.getenv('DB_NAME', 'sistema_salud')}
        """)
    
    with col2:
        st.info(f"""
        **Fecha actual:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        **Tema activo:** {'Oscuro' if st.session_state.theme == 'dark' else 'Claro'}
        **Total de tablas:** {total_tables}
        """)

# Página de análisis de datos
def page_analisis(connection):
    st.title("📊 Análisis de Datos")
    st.markdown("---")
    
    tables = get_tables(connection)
    selected_table = st.selectbox("Seleccionar tabla para analizar", tables)
    
    if selected_table:
        st.header(f"📋 Análisis de tabla: {selected_table}")
        
        stats = get_statistics(connection, selected_table)
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Registros", stats['total_registros'])
            col2.metric("Total Columnas", stats['total_columnas'])
            col3.metric("Memoria Usada", stats['memoria_usada'])
            col4.metric("Tabla", selected_table)
            
            st.markdown("---")
            
            st.subheader("📌 Información de Columnas")
            col_info = get_table_info(connection, selected_table)
            if col_info:
                col_df = pd.DataFrame(col_info, columns=['Columna', 'Tipo', 'Null', 'Key', 'Default', 'Extra'])
                st.dataframe(col_df, use_container_width=True)
            
            st.markdown("---")
            
            st.subheader("📊 Datos de la Tabla")
            df = get_table_data(connection, selected_table)
            
            if not df.empty:
                # Paginación
                st.session_state.page_num = 1
                paginated_df = paginate_data(df, page_size=10)
                st.dataframe(paginated_df, use_container_width=True)
                
                # Exportación
                st.markdown("---")
                st.subheader("📥 Exportar Datos")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = export_data(df, 'csv')
                    st.download_button(
                        label="Descargar CSV",
                        data=csv_data,
                        file_name=f"{selected_table}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    try:
                        excel_data = export_data(df, 'excel')
                        st.download_button(
                            label="Descargar Excel",
                            data=excel_data,
                            file_name=f"{selected_table}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except:
                        st.warning("Excel no disponible (requiere openpyxl)")
                
                st.markdown("---")
                st.subheader("📈 Estadísticas Descriptivas")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Columnas Numéricas:**")
                    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                    if len(numeric_cols) > 0:
                        st.dataframe(df[numeric_cols].describe(), use_container_width=True)
                    else:
                        st.info("No hay columnas numéricas")
                
                with col2:
                    st.write("**Columnas Categóricas:**")
                    categorical_cols = df.select_dtypes(include=['object']).columns
                    if len(categorical_cols) > 0:
                        for col in categorical_cols[:5]:
                            st.write(f"**{col}:**")
                            st.write(df[col].value_counts().head(10))
                    else:
                        st.info("No hay columnas categóricas")
                
                st.markdown("---")
                st.subheader("❓ Análisis de Valores Nulos")
                null_counts = df.isnull().sum()
                null_percentages = (df.isnull().sum() / len(df)) * 100
                
                null_df = pd.DataFrame({
                    'Columna': null_counts.index,
                    'Valores Nulos': null_counts.values,
                    'Porcentaje': null_percentages.values
                })
                
                if null_df['Valores Nulos'].sum() > 0:
                    st.dataframe(null_df, use_container_width=True)
                    
                    fig_null = px.bar(
                        null_df,
                        x='Columna',
                        y='Porcentaje',
                        title='Porcentaje de Valores Nulos por Columna'
                    )
                    st.plotly_chart(fig_null, use_container_width=True)
                else:
                    st.success("✅ No hay valores nulos en la tabla")
            else:
                st.warning("La tabla está vacía")

# Página de visualizaciones
def page_visualizaciones(connection):
    st.title("📈 Visualizaciones")
    st.markdown("---")
    
    tables = get_tables(connection)
    selected_table = st.selectbox("Seleccionar tabla para visualizar", tables)
    
    if selected_table:
        st.header(f"📉 Visualizaciones de: {selected_table}")
        
        df = get_table_data(connection, selected_table)
        
        if not df.empty:
            charts = generate_charts(df, selected_table)
            
            if charts:
                for chart_type, fig in charts:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No se pudieron generar gráficos con los datos actuales")
        else:
            st.warning("La tabla está vacía")

# Página de búsqueda avanzada
def page_busqueda(connection):
    st.title("🔍 Búsqueda Avanzada")
    st.markdown("---")
    
    tables = get_tables(connection)
    selected_table = st.selectbox("Seleccionar tabla para buscar", tables)
    
    if selected_table:
        st.header(f"🔎 Buscar en: {selected_table}")
        
        search_term = st.text_input("Término de búsqueda")
        
        col_info = get_table_info(connection, selected_table)
        text_columns = [col[0] for col in col_info if 'text' in col[1].lower() or 'char' in col[1].lower() or 'varchar' in col[1].lower()]
        
        if text_columns:
            selected_columns = st.multiselect("Columnas a buscar (dejar vacío para todas)", text_columns)
        else:
            st.warning("No hay columnas de texto en esta tabla")
            selected_columns = None
        
        if st.button("🔍 Buscar"):
            if search_term:
                results = advanced_search(connection, selected_table, search_term, selected_columns if selected_columns else None)
                
                if not results.empty:
                    st.success(f"Se encontraron {len(results)} resultados")
                    st.dataframe(results, use_container_width=True)
                else:
                    st.warning("No se encontraron resultados")
            else:
                st.warning("Por favor ingrese un término de búsqueda")

# Página de gestión de datos
def page_gestion(connection):
    st.title("📝 Gestión de Datos")
    st.markdown("---")
    
    tables = get_tables(connection)
    
    st.subheader("📥 Insertar Nuevo Registro")
    
    tablas_para_insertar = ['atenciones', 'pacientes', 'prestadores', 'profesionales', 'ubicaciones']
    tablas_disponibles = [t for t in tablas_para_insertar if t in tables]
    
    if not tablas_disponibles:
        st.warning("No hay tablas disponibles para insertar registros")
    else:
        selected_table = st.selectbox("Seleccionar tabla para insertar", tablas_disponibles)
        
        if selected_table:
            st.subheader(f"Insertar en tabla: {selected_table}")
            
            col_info = get_table_info(connection, selected_table)
            
            if col_info:
                st.write("Complete los campos marcados con * (obligatorios):")
                
                with st.form(key=f"insert_form_{selected_table}"):
                    form_data = get_insert_form(connection, selected_table, col_info)
                    
                    submit_button = st.form_submit_button("Insertar Registro")
                    
                    if submit_button:
                        filtered_data = {k: v for k, v in form_data.items() if v is not None and v != ''}
                        
                        if filtered_data:
                            success, message = insert_record(connection, selected_table, filtered_data)
                            
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.warning("Por favor complete al menos un campo")

# Página de configuración
def page_configuracion():
    st.title("⚙️ Configuración")
    st.markdown("---")
    
    st.subheader("🔗 Conexión a Base de Datos")
    
    db_host = st.text_input("Host", value=os.getenv('DB_HOST', 'localhost'))
    db_user = st.text_input("Usuario", value=os.getenv('DB_USER', 'root'))
    db_password = st.text_input("Contraseña", value=os.getenv('DB_PASSWORD', ''), type="password")
    db_name = st.text_input("Base de datos", value=os.getenv('DB_NAME', 'test_db'))
    
    if st.button("💾 Guardar Configuración"):
        try:
            with open('.env', 'w') as f:
                f.write(f"DB_HOST={db_host}\n")
                f.write(f"DB_USER={db_user}\n")
                f.write(f"DB_PASSWORD={db_password}\n")
                f.write(f"DB_NAME={db_name}\n")
            st.success("✅ Configuración guardada exitosamente")
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar configuración: {e}")
    
    st.markdown("---")
    st.subheader("🎨 Preferencias de Visualización")
    
    if st.button("🔄 Restablecer Página"):
        st.session_state.page = 'inicio'
        st.rerun()

# Función principal
def main():
    # Configuración de conexión en sidebar
    st.sidebar.header("🔗 Conexión MySQL")
    db_host = st.sidebar.text_input("Host", value=os.getenv('DB_HOST', 'localhost'))
    db_user = st.sidebar.text_input("Usuario", value=os.getenv('DB_USER', 'root'))
    db_password = st.sidebar.text_input("Contraseña", value=os.getenv('DB_PASSWORD', ''), type="password")
    db_name = st.sidebar.text_input("Base de datos", value=os.getenv('DB_NAME', 'test_db'))
    
    if st.sidebar.button("🔌 Conectar"):
        try:
            connection = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name
            )
            if connection.is_connected():
                st.session_state.connection = connection
                st.sidebar.success("✅ Conectado exitosamente")
        except Error as e:
            st.sidebar.error(f"❌ Error de conexión: {e}")
    
    if st.sidebar.button("🔌 Desconectar"):
        if 'connection' in st.session_state:
            st.session_state.connection.close()
            del st.session_state.connection
            st.sidebar.success("Desconectado")
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # Navegación principal
    current_page = main_navigation()
    
    # Ejecutar página correspondiente
    if 'connection' not in st.session_state or not st.session_state.connection.is_connected():
        st.warning("⚠️ Por favor, conecte a la base de datos desde la sidebar")
        st.info("Configure los parámetros de conexión y haga clic en 'Conectar'")
    else:
        connection = st.session_state.connection
        
        if current_page == 'inicio':
            page_inicio(connection)
        elif current_page == 'analisis':
            page_analisis(connection)
        elif current_page == 'visualizaciones':
            page_visualizaciones(connection)
        elif current_page == 'busqueda':
            page_busqueda(connection)
        elif current_page == 'gestion':
            page_gestion(connection)
        elif current_page == 'configuracion':
            page_configuracion()

if __name__ == "__main__":
    main()

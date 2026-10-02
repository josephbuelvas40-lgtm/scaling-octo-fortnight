import pandas as pd
import numpy as np
from datetime import datetime
import io


class ETLProcessor:
    
    def __init__(self):
        self.log = []
    
    def extract_data(self, connection, source_type, config):
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
    
    def transform_data(self, df, transformations):
        try:
            transformed_df = df.copy()
            transformations_applied = []
            
            for transform in transformations:
                transform_type = transform.get('type')
                
                if transform_type == 'clean_nulls':
                    strategy = transform.get('strategy', 'drop')
                    if strategy == 'drop':
                        original_len = len(transformed_df)
                        transformed_df = transformed_df.dropna()
                        removed = original_len - len(transformed_df)
                        transformations_applied.append(f"Eliminados {removed} valores nulos")
                    elif strategy == 'fill_mean':
                        numeric_cols = transformed_df.select_dtypes(include=[np.number]).columns
                        transformed_df[numeric_cols] = transformed_df[numeric_cols].fillna(transformed_df[numeric_cols].mean())
                        transformations_applied.append("Rellenados nulos con media")
                    elif strategy == 'fill_zero':
                        transformed_df = transformed_df.fillna(0)
                        transformations_applied.append("Rellenados nulos con cero")
                
                elif transform_type == 'remove_duplicates':
                    original_len = len(transformed_df)
                    transformed_df = transformed_df.drop_duplicates()
                    removed = original_len - len(transformed_df)
                    transformations_applied.append(f"Eliminados {removed} duplicados")
                
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
                        original_len = len(transformed_df)
                        
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
                        
                        filtered = original_len - len(transformed_df)
                        transformations_applied.append(f"Filtrado por {column} {condition} {value} ({filtered} registros)")
                
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
                    transformations_applied.append(f"Renombradas {len(mapping)} columnas")
                
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
                
                elif transform_type == 'standardize_text':
                    column = transform.get('column')
                    operation = transform.get('operation', 'lower')
                    
                    if column in transformed_df.columns:
                        if operation == 'lower':
                            transformed_df[column] = transformed_df[column].astype(str).str.lower()
                        elif operation == 'upper':
                            transformed_df[column] = transformed_df[column].astype(str).str.upper()
                        elif operation == 'title':
                            transformed_df[column] = transformed_df[column].astype(str).str.title()
                        elif operation == 'strip':
                            transformed_df[column] = transformed_df[column].astype(str).str.strip()
                        
                        transformations_applied.append(f"Columna {column} estandarizada a {operation}")
                
                elif transform_type == 'normalize_numeric':
                    column = transform.get('column')
                    method = transform.get('method', 'minmax')
                    
                    if column in transformed_df.columns and pd.api.types.is_numeric_dtype(transformed_df[column]):
                        if method == 'minmax':
                            min_val = transformed_df[column].min()
                            max_val = transformed_df[column].max()
                            if max_val != min_val:
                                transformed_df[column] = (transformed_df[column] - min_val) / (max_val - min_val)
                        elif method == 'zscore':
                            mean_val = transformed_df[column].mean()
                            std_val = transformed_df[column].std()
                            if std_val != 0:
                                transformed_df[column] = (transformed_df[column] - mean_val) / std_val
                        
                        transformations_applied.append(f"Columna {column} normalizada usando {method}")
            
            return transformed_df, transformations_applied
        
        except Exception as e:
            return df, [f"Error en transformación: {e}"]
    
    def load_data(self, df, destination_type, config, connection=None):
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
    
    def run_pipeline(self, connection, extract_config, transformations, load_config):
        self.log = []
        
        extracted_df, extract_msg = self.extract_data(connection, extract_config['source_type'], extract_config)
        self.log.append(("EXTRACT", extract_msg))
        
        if extracted_df.empty:
            return pd.DataFrame(), self.log
        
        if transformations:
            transformed_df, transform_msgs = self.transform_data(extracted_df, transformations)
            for msg in transform_msgs:
                self.log.append(("TRANSFORM", msg))
        else:
            transformed_df = extracted_df
            self.log.append(("TRANSFORM", "Sin transformaciones"))
        
        load_msg = self.load_data(transformed_df, load_config['destination_type'], load_config, connection)
        self.log.append(("LOAD", load_msg))
        
        return transformed_df, self.log
    
    def get_log(self):
        return self.log
    
    def clear_log(self):
        self.log = []


def export_data(df, format='csv'):
    if format == 'csv':
        return df.to_csv(index=False).encode('utf-8')
    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()


def get_data_quality_report(df):
    report = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'null_counts': df.isnull().sum().to_dict(),
        'null_percentages': (df.isnull().sum() / len(df) * 100).to_dict(),
        'duplicate_rows': df.duplicated().sum(),
        'duplicate_percentage': (df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0,
        'data_types': df.dtypes.astype(str).to_dict(),
        'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
    }
    
    return report


def suggest_transformations(df):
    suggestions = []
    
    null_percentage = (df.isnull().sum() / len(df) * 100)
    high_null_cols = null_percentage[null_percentage > 10].index.tolist()
    if high_null_cols:
        suggestions.append({
            'type': 'clean_nulls',
            'reason': f"Columnas con alto porcentaje de nulos: {high_null_cols}",
            'recommendation': 'Considerar eliminar filas o rellenar con media/mediana'
        })
    
    if df.duplicated().sum() > 0:
        suggestions.append({
            'type': 'remove_duplicates',
            'reason': f"Se detectaron {df.duplicated().sum()} filas duplicadas",
            'recommendation': 'Eliminar duplicados para mejorar calidad de datos'
        })
    
    text_cols = df.select_dtypes(include=['object']).columns
    for col in text_cols:
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio < 0.1 and df[col].nunique() > 1:
            suggestions.append({
                'type': 'convert_types',
                'column': col,
                'target_type': 'category',
                'reason': f"Columna {col} tiene baja cardinalidad ({df[col].nunique()} valores únicos)",
                'recommendation': 'Convertir a tipo category para optimizar memoria'
            })
    
    return suggestions
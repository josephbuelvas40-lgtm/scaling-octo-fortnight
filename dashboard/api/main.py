from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import sys
import io
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'etl'))
from etl import ETLProcessor, export_data, get_data_quality_report, suggest_transformations

load_dotenv()

app = FastAPI(
    title="Dashboard MySQL API",
    description="API REST para análisis de datos y procesamiento ETL",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionConfig(BaseModel):
    host: str = Field(default="localhost")
    user: str = Field(default="root")
    password: str = Field(default="")
    database: str = Field(default="sistema_salud")

class ExtractConfig(BaseModel):
    source_type: str = Field(...)
    table_name: Optional[str] = Field(None)
    query: Optional[str] = Field(None)

class TransformConfig(BaseModel):
    type: str = Field(...)
    strategy: Optional[str] = Field(None)
    column: Optional[str] = Field(None)
    target_type: Optional[str] = Field(None)
    condition: Optional[str] = Field(None)
    value: Optional[Any] = Field(None)
    group_by: Optional[str] = Field(None)
    agg_func: Optional[str] = Field(None)
    mapping: Optional[Dict[str, str]] = Field(None)
    column_name: Optional[str] = Field(None)
    expression: Optional[str] = Field(None)
    operation: Optional[str] = Field(None)
    method: Optional[str] = Field(None)

class LoadConfig(BaseModel):
    destination_type: str = Field(...)
    table_name: Optional[str] = Field(None)
    if_exists: Optional[str] = Field(default="append")
    filename: Optional[str] = Field(None)

class ETLRequest(BaseModel):
    connection: ConnectionConfig
    extract: ExtractConfig
    transformations: List[TransformConfig] = []
    load: LoadConfig

class TableAnalysisRequest(BaseModel):
    connection: ConnectionConfig
    table_name: str

class SearchRequest(BaseModel):
    connection: ConnectionConfig
    table_name: str
    search_term: str
    columns: Optional[List[str]] = None

def get_connection(config: ConnectionConfig):
    try:
        connection = mysql.connector.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database
        )
        if connection.is_connected():
            return connection
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {e}")

def get_tables(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        return tables
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tablas: {e}")

def get_table_data(connection, table_name, limit=1000):
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos: {e}")

def get_table_info(connection, table_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        return columns
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener información: {e}")

@app.get("/")
async def root():
    return {
        "message": "Dashboard MySQL API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "tables": "/api/tables",
            "etl": "/api/etl"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if os.getenv('DB_HOST') else "not configured"
    }

@app.post("/api/test-connection")
async def test_connection(config: ConnectionConfig):
    try:
        connection = get_connection(config)
        connection.close()
        return {"status": "success", "message": "Conexión exitosa"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tables")
async def get_database_tables(config: ConnectionConfig):
    try:
        connection = get_connection(config)
        tables = get_tables(connection)
        connection.close()
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/table/{table_name}")
async def get_table_details(table_name: str, config: ConnectionConfig):
    try:
        connection = get_connection(config)
        col_info = get_table_info(connection, table_name)
        col_df = pd.DataFrame(col_info, columns=['Columna', 'Tipo', 'Null', 'Key', 'Default', 'Extra'])
        df = get_table_data(connection, table_name)
        
        stats = {
            'total_registros': len(df),
            'total_columnas': len(df.columns),
            'columnas': list(df.columns),
            'tipos_datos': df.dtypes.astype(str).to_dict(),
            'memoria_usada': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
        }
        
        connection.close()
        
        return {
            "table_name": table_name,
            "columns": col_df.to_dict(orient='records'),
            "statistics": stats,
            "data_preview": df.head(10).to_dict(orient='records'),
            "total_rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/table/{table_name}/data")
async def get_table_data_endpoint(table_name: str, config: ConnectionConfig, limit: int = 1000):
    try:
        connection = get_connection(config)
        df = get_table_data(connection, table_name, limit)
        connection.close()
        
        return {
            "table_name": table_name,
            "data": df.to_dict(orient='records'),
            "rows": len(df),
            "columns": list(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/{table_name}")
async def analyze_table(table_name: str, config: ConnectionConfig):
    try:
        connection = get_connection(config)
        df = get_table_data(connection, table_name)
        
        numeric_stats = {}
        categorical_stats = {}
        
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            numeric_stats = df[numeric_cols].describe().to_dict()
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols[:5]:
            categorical_stats[col] = df[col].value_counts().head(10).to_dict()
        
        null_analysis = {
            'null_counts': df.isnull().sum().to_dict(),
            'null_percentages': (df.isnull().sum() / len(df) * 100).to_dict()
        }
        
        connection.close()
        
        return {
            "table_name": table_name,
            "numeric_statistics": numeric_stats,
            "categorical_statistics": categorical_stats,
            "null_analysis": null_analysis,
            "total_rows": len(df),
            "total_columns": len(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quality-report/{table_name}")
async def get_quality_report(table_name: str, config: ConnectionConfig):
    try:
        connection = get_connection(config)
        df = get_table_data(connection, table_name)
        connection.close()
        
        report = get_data_quality_report(df)
        suggestions = suggest_transformations(df)
        
        return {
            "table_name": table_name,
            "quality_report": report,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_data(request: SearchRequest):
    try:
        connection = get_connection(request.connection)
        
        if request.columns:
            conditions = []
            for col in request.columns:
                conditions.append(f"{col} LIKE '%{request.search_term}%'")
            query = f"SELECT * FROM {request.table_name} WHERE {' OR '.join(conditions)}"
        else:
            col_info = get_table_info(connection, request.table_name)
            text_columns = [col[0] for col in col_info if 'text' in col[1].lower() or 'char' in col[1].lower() or 'varchar' in col[1].lower()]
            
            if text_columns:
                conditions = [f"{col} LIKE '%{request.search_term}%'" for col in text_columns]
                query = f"SELECT * FROM {request.table_name} WHERE {' OR '.join(conditions)}"
            else:
                query = f"SELECT * FROM {request.table_name}"
        
        df = pd.read_sql(query, connection)
        connection.close()
        
        return {
            "table_name": request.table_name,
            "search_term": request.search_term,
            "results": df.to_dict(orient='records'),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/etl")
async def run_etl_pipeline(request: ETLRequest):
    try:
        connection = get_connection(request.connection)
        etl = ETLProcessor()
        
        transformations = [t.dict() for t in request.transformations]
        
        result_df, log = etl.run_pipeline(
            connection,
            request.extract.dict(),
            transformations,
            request.load.dict()
        )
        
        connection.close()
        
        return {
            "status": "success",
            "result_rows": len(result_df),
            "log": [{"phase": phase, "message": msg} for phase, msg in log],
            "data_preview": result_df.head(5).to_dict(orient='records') if not result_df.empty else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/etl/extract")
async def extract_only(config: ConnectionConfig, extract_config: ExtractConfig):
    try:
        connection = get_connection(config)
        etl = ETLProcessor()
        
        df, message = etl.extract_data(connection, extract_config.source_type, extract_config.dict())
        connection.close()
        
        return {
            "status": "success",
            "message": message,
            "rows": len(df),
            "columns": list(df.columns),
            "data_preview": df.head(5).to_dict(orient='records') if not df.empty else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/etl/transform")
async def transform_only(data: List[Dict], transformations: List[TransformConfig]):
    try:
        df = pd.DataFrame(data)
        etl = ETLProcessor()
        
        transform_list = [t.dict() for t in transformations]
        result_df, messages = etl.transform_data(df, transform_list)
        
        return {
            "status": "success",
            "transformations": messages,
            "rows": len(result_df),
            "data_preview": result_df.head(5).to_dict(orient='records') if not result_df.empty else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/{file_type}")
async def upload_file(file_type: str, file: UploadFile = File(...)):
    try:
        if file_type not in ['csv', 'excel', 'json']:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado")
        
        contents = await file.read()
        
        if file_type == 'csv':
            df = pd.read_csv(io.BytesIO(contents))
        elif file_type == 'excel':
            df = pd.read_excel(io.BytesIO(contents))
        elif file_type == 'json':
            df = pd.read_json(io.BytesIO(contents))
        
        return {
            "status": "success",
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "data_preview": df.head(5).to_dict(orient='records') if not df.empty else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/{file_type}")
async def export_sample(file_type: str):
    try:
        sample_data = {
            'id': [1, 2, 3],
            'nombre': ['Juan', 'María', 'Carlos'],
            'edad': [25, 30, 35],
            'ciudad': ['Madrid', 'Barcelona', 'Valencia']
        }
        df = pd.DataFrame(sample_data)
        
        if file_type == 'csv':
            output = df.to_csv(index=False)
            return {"status": "success", "data": output, "type": "csv"}
        elif file_type == 'json':
            output = df.to_json(orient='records')
            return {"status": "success", "data": output, "type": "json"}
        else:
            raise HTTPException(status_code=400, detail="Tipo de exportación no soportado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_api_stats():
    return {
        "version": "1.0.0",
        "endpoints": len(app.routes),
        "uptime": "active",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
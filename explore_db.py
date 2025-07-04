import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

def explore_database():
    try:
        # Conectar a la base de datos
        connection = pymysql.connect(
            host='shortline.proxy.rlwy.net',
            port=27903,
            user='root',
            password='RuXPoVZdquGlXEBAyxYfjcMlJThKwWBl',
            database='railway'
        )

        cursor = connection.cursor()

        # Obtener todas las tablas
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()

        print('=== ESTRUCTURA DE LA BASE DE DATOS ===')
        print()

        for table in tables:
            table_name = table[0]
            print(f'--- TABLA: {table_name} ---')
            
            # Obtener estructura de la tabla
            cursor.execute(f'DESCRIBE {table_name}')
            columns = cursor.fetchall()
            
            for column in columns:
                field, type_info, null, key, default, extra = column
                null_info = "NULL" if null == "YES" else "NOT NULL"
                key_info = "PRIMARY" if key == "PRI" else ""
                default_info = f"DEFAULT {default}" if default else ""
                
                print(f'  {field}: {type_info} {null_info} {key_info} {default_info}')
            
            print()

        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    explore_database() 
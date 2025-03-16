import mysql.connector
import pandas as pd
from sqlalchemy import create_engine, inspect
from sklearn import datasets

# Configuración de la base de datos MySQL
db_config = {
    "host": "10.43.101.189",
    "port": 3306,
    "user": "taller-mlflow",
    "password": "mlflow",
    "database": "taller",
}

# Eliminamos la tabla 'iris_raw' si ya existe
try:
    with mysql.connector.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS iris_raw;")
            conn.commit()
    print("Tabla 'iris_raw' eliminada con éxito (si existía).")
except mysql.connector.Error as err:
    print(f"Error: {err}")

# Cargamos el conjunto de datos Iris
datos_iris = datasets.load_iris()

# Convertimos los datos en un DataFrame de pandas
iris = pd.DataFrame(data=datos_iris.data, columns=datos_iris.feature_names)

# Agregamos la columna de especies con nombres de categorías
iris['species'] = pd.Categorical.from_codes(
    datos_iris.target, 
    categories=datos_iris.target_names
)

# Verificamos el tipo de datos de la columna 'species'
print(f"Tipo de dato de 'species': {iris['species'].dtype}")
print(iris['species'].value_counts())

# Creamos el motor de conexión a la base de datos
engine = create_engine(
    f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
)

# Cargamos los datos en la base de datos MySQL
iris.to_sql('iris_raw', engine, if_exists='replace', index=False)

# Leemos los datos preprocesados desde MySQL
df = pd.read_sql_table('iris_raw', engine)

# Eliminamos duplicados y valores nulos
df_clean = df.drop_duplicates().dropna()

# Convertimos la columna 'species' a valores numéricos
species_mapping = {species: idx for idx, species in enumerate(sorted(df_clean['species'].unique()))}
df_clean['species'] = df_clean['species'].map(species_mapping)

# Guardamos los datos limpios en una nueva tabla en MySQL
df_clean.to_sql('iris_cleaned', engine, if_exists='replace', index=False)

print("Proceso completado: Datos limpios almacenados en 'iris_cleaned'.")

# Crear el inspector de la base de datos
inspector = inspect(engine)

# Obtener la lista de tablas en la base de datos 'taller'
tables = inspector.get_table_names()

# Imprimir la lista de tablas
print("Tablas en la base de datos 'taller':", tables)
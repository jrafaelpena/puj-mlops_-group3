CREATE DATABASE IF NOT EXISTS train_data;
CREATE USER IF NOT EXISTS 'airflow'@'%' IDENTIFIED BY 'airflow';
GRANT ALL PRIVILEGES ON train_data.* TO 'airflow'@'%';
FLUSH PRIVILEGES;

USE train_data;
DROP TABLE IF EXISTS forest_cover_data;

CREATE TABLE forest_cover_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Elevation FLOAT,
    Aspect FLOAT,
    Slope FLOAT,
    Horizontal_Distance_To_Hydrology FLOAT,
    Vertical_Distance_To_Hydrology FLOAT,
    Horizontal_Distance_To_Roadways FLOAT,
    Hillshade_9am FLOAT,
    Hillshade_Noon FLOAT,
    Hillshade_3pm FLOAT,
    Horizontal_Distance_To_Fire_Points FLOAT,
    Wilderness_Area VARCHAR(50),
    Soil_Type VARCHAR(50),
    Cover_Type VARCHAR(50),
    batch_number INT,
    timestamp DATETIME,
    UNIQUE KEY unique_record (
        Elevation, Aspect, Slope, 
        Horizontal_Distance_To_Hydrology, Vertical_Distance_To_Hydrology,
        Horizontal_Distance_To_Roadways,
        Hillshade_9am, Hillshade_Noon, Hillshade_3pm,
        Horizontal_Distance_To_Fire_Points, 
        Wilderness_Area, Soil_Type, Cover_Type
    )
);
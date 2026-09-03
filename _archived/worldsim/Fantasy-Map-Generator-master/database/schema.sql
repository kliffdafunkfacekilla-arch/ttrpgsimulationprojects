CREATE TABLE macro_groups (
    id SERIAL PRIMARY KEY,
    population FLOAT,
    chaos_level FLOAT,
    pressure FLOAT,
    magistar_id VARCHAR(255),
    is_active BOOLEAN,
    weather VARCHAR(255),
    geom GEOMETRY(Geometry, 4326), -- Using PostGIS standard representation
    
    -- Well-Being and Social Stats
    physical_well_being FLOAT DEFAULT 1.0,
    mental_well_being FLOAT DEFAULT 1.0,
    crime_level FLOAT DEFAULT 0.0,
    discontent FLOAT DEFAULT 0.0,
    security_rating FLOAT DEFAULT 0.5,
    food_supply FLOAT DEFAULT 0.5,
    safety_rating FLOAT DEFAULT 0.5,
    
    -- Infrastructure and Gathering Buildings
    camps_count INT DEFAULT 0,
    mines_count INT DEFAULT 0,
    docks_count INT DEFAULT 0,
    farms_count INT DEFAULT 0,
    watchtowers_count INT DEFAULT 0,
    walls_count INT DEFAULT 0,
    barracks_count INT DEFAULT 0
);

CREATE TABLE cells (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Geometry, 4326)
);

CREATE TABLE species (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    homeland VARCHAR(255),
    traits TEXT,
    societal_function TEXT
);

CREATE TABLE factions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    base_of_operations VARCHAR(255),
    key_leaders VARCHAR(255),
    description TEXT,
    mechanics TEXT,
    special_sight_protocol TEXT
);

CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    origin TEXT,
    physical_properties TEXT,
    applications TEXT
);

CREATE TABLE produced_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    tier INT NOT NULL,
    composition TEXT,
    purpose TEXT,
    user_mechanics TEXT
);

CREATE TABLE wildlife (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    scientific_name VARCHAR(255),
    role VARCHAR(255),
    habitat VARCHAR(255),
    danger_level INT,
    traits TEXT,
    utility TEXT
);

CREATE TABLE flora (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    classification VARCHAR(255),
    habitat VARCHAR(255),
    properties TEXT,
    applications TEXT
);

CREATE TABLE rivers (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Geometry, 4326)
);

CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Geometry, 4326)
);

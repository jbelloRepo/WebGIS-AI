-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create water_mains table
CREATE TABLE IF NOT EXISTS water_mains (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,               -- City name
    dataset_type VARCHAR(100) NOT NULL,       -- Type of dataset
    object_id INTEGER UNIQUE NOT NULL,        -- Unique object ID
    watmain_id INTEGER,                       -- Water main ID
    status VARCHAR(50) DEFAULT 'UNKNOWN',     -- Status (e.g., ACTIVE, ABANDONED)
    pressure_zone VARCHAR(50) DEFAULT 'UNKNOWN', -- Pressure zone
    roadsegment_id INTEGER,                   -- Related road segment ID
    map_label VARCHAR(255),                   -- Descriptive label
    category VARCHAR(50) DEFAULT 'TREATED',   -- Treated/Untreated category
    pipe_size NUMERIC DEFAULT 0,              -- Pipe size in mm
    material VARCHAR(100) DEFAULT 'UNKNOWN',  -- Pipe material
    lined VARCHAR(20) DEFAULT 'NO',           -- Lined or not
    lined_date TIMESTAMP,                     -- Date lining was done
    lined_material VARCHAR(50) DEFAULT 'NONE', -- Material for lining
    installation_date TIMESTAMP,             -- Installation date
    acquisition VARCHAR(50),                 -- Acquisition type
    consultant VARCHAR(250),                 -- Consultant name
    ownership VARCHAR(100) DEFAULT 'UNKNOWN', -- Ownership details
    bridge_main VARCHAR(1) DEFAULT 'N',       -- Bridge main indicator
    bridge_details VARCHAR(250),             -- Details about the bridge
    criticality INTEGER DEFAULT -1,          -- Criticality level
    rel_cleaning_area VARCHAR(10) DEFAULT '0', -- Cleaning area
    rel_cleaning_subarea VARCHAR(10) DEFAULT '0', -- Cleaning subarea
    undersized VARCHAR(1) DEFAULT 'N',       -- Undersized indicator
    shallow_main VARCHAR(1) DEFAULT 'N',     -- Shallow pipe indicator
    condition_score NUMERIC DEFAULT -1,      -- Condition score
    oversized VARCHAR(1) DEFAULT 'N',        -- Oversized pipe indicator
    cleaned VARCHAR(1) DEFAULT 'N',          -- Cleaned or not
    shape_length NUMERIC,                    -- Length of the geometry
    geometry GEOMETRY(LineString, 4326),     -- Spatial geometry in WGS84
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Creation timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Update timestamp
);

-- Create indexes for efficient querying
CREATE INDEX idx_water_mains_city ON water_mains(city);
CREATE INDEX idx_water_mains_object_id ON water_mains(object_id);
CREATE INDEX idx_water_mains_material ON water_mains(material);
CREATE INDEX idx_water_mains_status ON water_mains(status);
CREATE INDEX idx_water_mains_geometry ON water_mains USING GIST(geometry);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_water_mains_updated_at
    BEFORE UPDATE ON water_mains
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

import psycopg2
from psycopg2.extras import Json
from db_conn_config import get_db_connection
import json

def update_water_mains_data(city, dataset_type, data):
    """Update water mains data in the database."""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        for feature in data.get('features', []):
            attributes = feature.get("attributes", {})
            geometry = feature.get("geometry", {})
            
            # Extract timestamps
            lined_date = attributes.get('LINED_DATE')
            installation_date = attributes.get('INSTALLATION_DATE')

            # Convert geometry paths to GeoJSON format
            geojson = {
                "type": "LineString",
                "coordinates": geometry.get('paths', [[]])[0]
            }

            cursor.execute("""
                INSERT INTO water_mains (
                    city, dataset_type, object_id, watmain_id, status, pressure_zone,
                    roadsegment_id, map_label, category, pipe_size, material,
                    lined, lined_date, lined_material, installation_date, acquisition,
                    consultant, ownership, bridge_main, bridge_details, criticality,
                    rel_cleaning_area, rel_cleaning_subarea, undersized, shallow_main,
                    condition_score, oversized, cleaned, shape_length, geometry
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    CASE WHEN %s IS NOT NULL THEN to_timestamp(%s::bigint/1000) ELSE NULL END,
                    %s,
                    CASE WHEN %s IS NOT NULL THEN to_timestamp(%s::bigint/1000) ELSE NULL END,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    ST_GeomFromGeoJSON(%s)
                )
                ON CONFLICT (object_id) DO UPDATE 
                SET watmain_id = EXCLUDED.watmain_id,
                    status = EXCLUDED.status,
                    pressure_zone = EXCLUDED.pressure_zone,
                    roadsegment_id = EXCLUDED.roadsegment_id,
                    map_label = EXCLUDED.map_label,
                    category = EXCLUDED.category,
                    pipe_size = EXCLUDED.pipe_size,
                    material = EXCLUDED.material,
                    lined = EXCLUDED.lined,
                    lined_date = EXCLUDED.lined_date,
                    lined_material = EXCLUDED.lined_material,
                    installation_date = EXCLUDED.installation_date,
                    acquisition = EXCLUDED.acquisition,
                    consultant = EXCLUDED.consultant,
                    ownership = EXCLUDED.ownership,
                    bridge_main = EXCLUDED.bridge_main,
                    bridge_details = EXCLUDED.bridge_details,
                    criticality = EXCLUDED.criticality,
                    rel_cleaning_area = EXCLUDED.rel_cleaning_area,
                    rel_cleaning_subarea = EXCLUDED.rel_cleaning_subarea,
                    undersized = EXCLUDED.undersized,
                    shallow_main = EXCLUDED.shallow_main,
                    condition_score = EXCLUDED.condition_score,
                    oversized = EXCLUDED.oversized,
                    cleaned = EXCLUDED.cleaned,
                    shape_length = EXCLUDED.shape_length,
                    geometry = EXCLUDED.geometry;
            """, (
                city, dataset_type, attributes.get('OBJECTID'), attributes.get('WATMAINID'),
                attributes.get('STATUS'), attributes.get('PRESSURE_ZONE'),
                attributes.get('ROADSEGMENTID'), attributes.get('MAP_LABEL'),
                attributes.get('CATEGORY'), attributes.get('PIPE_SIZE'),
                attributes.get('MATERIAL'), attributes.get('LINED'),
                lined_date, lined_date,
                attributes.get('LINED_MATERIAL'),
                installation_date, installation_date,
                attributes.get('ACQUISITION'), attributes.get('CONSULTANT'),
                attributes.get('OWNERSHIP'), attributes.get('BRIDGE_MAIN'),
                attributes.get('BRIDGE_DETAILS'), attributes.get('CRITICALITY'),
                attributes.get('REL_CLEANING_AREA'), attributes.get('REL_CLEANING_SUBAREA'),
                attributes.get('UNDERSIZED'), attributes.get('SHALLOW_MAIN'),
                attributes.get('CONDITION_SCORE'), attributes.get('OVERSIZED'),
                attributes.get('CLEANED'), attributes.get('Shape__Length'),
                json.dumps(geojson)
            ))

        connection.commit()

    except Exception as e:
        if connection:
            connection.rollback()
        raise e

    finally:
        if connection:
            connection.close() 
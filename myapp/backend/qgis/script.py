import platform
import time
from qgis.core import (
    QgsApplication,
    QgsDataSourceUri,
    QgsVectorLayer,
    QgsProject,
    Qgis,
    QgsWkbTypes,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsLayoutItemMap,
    QgsLayoutItemLabel,
    QgsLayout,
    QgsLayoutExporter,
    QgsPrintLayout
)

def check_postgis_connection(retry_count=0, max_retries=5, initial_delay=5):
    qgs = None
    try:
        # Basic system info
        print(f"Python Version: {platform.python_version()}")
        print(f"Python Implementation: {platform.python_implementation()}")
        print(f"System: {platform.system()} {platform.release()}")

        # Initialize QGIS with more explicit error handling
        QgsApplication.setPrefixPath("/usr", True)
        qgs = QgsApplication([], False)
        qgs.initQgis()

        print("=== QGIS Application Info ===")
        print(f"QGIS Version: {Qgis.QGIS_VERSION}")

        # Build PostGIS connection
        uri = QgsDataSourceUri()
        uri.setConnection(
            "postgis-db-service",  # hostname
            "5432",                # port
            "gis_data",           # database name
            "gis_user",           # username
            "password"            # password
        )
        
        uri.setDataSource(
            "public",       # schema
            "water_mains",  # table
            "geometry",     # geometry column
            "",            # key column
            "id"           # primary key
        )

        # Load as vector layer
        layer = QgsVectorLayer(uri.uri(False), "water_mains", "postgres")

        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            feature_count = layer.featureCount()
            print("Successfully added layer to the project!")
            print(f"Feature count: {feature_count}")
            print(f"Layer CRS: {layer.crs().authid()}")
            print(f"Layer fields: {[field.name() for field in layer.fields()]}")
            
            if feature_count > 0:
                inspect_layer_features(layer)
                # Test print functionality
                create_print_layout(layer)
            
            if feature_count == 0 and retry_count < max_retries:
                print("No features found in the layer.")
                delay = initial_delay * (2 ** retry_count)
                print(f"Retrying in {delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                if qgs:
                    qgs.exitQgis()
                time.sleep(delay)
                return check_postgis_connection(retry_count + 1, max_retries, initial_delay)
                
            if qgs:
                qgs.exitQgis()
            return feature_count > 0
        else:
            print("ERROR: Could not connect to PostGIS or table does not exist.")
            print(f"Connection URI: {uri.uri(True)}")
            
            if retry_count < max_retries:
                delay = initial_delay * (2 ** retry_count)
                print(f"Retrying in {delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                if qgs:
                    qgs.exitQgis()
                time.sleep(delay)
                return check_postgis_connection(retry_count + 1, max_retries, initial_delay)
            else:
                print("Max retries reached. Exiting...")
                if qgs:
                    qgs.exitQgis()
                return False

    except Exception as e:
        print(f"Error in check_postgis_connection: {str(e)}")
        if qgs:
            try:
                qgs.exitQgis()
            except:
                pass
        return False

def inspect_layer_features(layer, max_features=1):
    """
    Inspect features of a QgsVectorLayer, including geometry and attributes.
    
    Args:
        layer (QgsVectorLayer): The layer to inspect
        max_features (int): Maximum number of features to inspect (default=1)
    """
    print("\n=== Inspecting Features ===")
    features = layer.getFeatures()
    
    feature_count = 0
    for feature in features:
        if max_features and feature_count >= max_features:
            break
            
        print(f"\nFeature ID: {feature.id()}")
        
        # Get geometry
        geom = feature.geometry()
        geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
        
        # Check geometry type and print details
        if geom.type() == QgsWkbTypes.PointGeometry:
            if geomSingleType:
                x = geom.asPoint()
                print(f"Point: {x}")
            else:
                x = geom.asMultiPoint()
                print(f"MultiPoint: {x}")
        elif geom.type() == QgsWkbTypes.LineGeometry:
            if geomSingleType:
                x = geom.asPolyline()
                print(f"Line: {x}")
                print(f"Length: {geom.length():.2f} units")
            else:
                x = geom.asMultiPolyline()
                print(f"MultiLine: {x}")
                print(f"Length: {geom.length():.2f} units")
        elif geom.type() == QgsWkbTypes.PolygonGeometry:
            if geomSingleType:
                x = geom.asPolygon()
                print(f"Polygon: {x}")
                print(f"Area: {geom.area():.2f} square units")
            else:
                x = geom.asMultiPolygon()
                print(f"MultiPolygon: {x}")
                print(f"Area: {geom.area():.2f} square units")
        else:
            print("Unknown or invalid geometry")
        
        # Print attributes
        print("Attributes:", feature.attributes())
        feature_count += 1
    
    if max_features == 1:
        print("\n(Showing only first feature for brevity)")

def create_print_layout(layer, output_path="/app/output/test_print.pdf"):
    """
    Create a simple print layout and export it to PDF.
    
    Args:
        layer (QgsVectorLayer): The layer to print
        output_path (str): Path where the PDF will be saved
    """
    try:
        # Create a new print layout
        project = QgsProject.instance()
        manager = project.layoutManager()
        
        # Remove any existing layouts with the same name
        for layout in manager.layouts():
            if layout.name() == "Test Print":
                manager.removeLayout(layout)
        
        # Create new layout
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName("Test Print")
        
        # Add layout to manager
        manager.addLayout(layout)
        
        # Create a map item
        map = QgsLayoutItemMap(layout)
        map.setRect(20, 20, 250, 250)
        
        # Set the map's extent to the layer's extent with some padding
        extent = layer.extent()
        extent.scale(1.1)  # Add 10% padding
        map.setExtent(extent)
        layout.addLayoutItem(map)
        
        # Export to PDF with basic settings
        settings = QgsLayoutExporter.PdfExportSettings()
        exporter = QgsLayoutExporter(layout)
        result = exporter.exportToPdf(output_path, settings)
        
        if result == QgsLayoutExporter.Success:
            print(f"PDF exported successfully to: {output_path}")
            return True
        else:
            print(f"PDF export failed with status: {result}")
            return False
            
    except Exception as e:
        print(f"Error creating print layout: {str(e)}")
        return False

if __name__ == "__main__":
    check_postgis_connection()

import platform
import time
from qgis.core import QgsApplication
import sys
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import (
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
    QgsPrintLayout,
    QgsLineSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsReadWriteContext,
    QgsRasterLayer,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsProcessingFeedback
)
from qgis.PyQt.QtXml import QDomDocument
import os

# Initialize QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

# Initialize Processing
sys.path.append('/usr/share/qgis/python/plugins')
import processing
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

class PrintingFeedback(QgsProcessingFeedback):
    """Simple feedback object that prints all messages to console"""
    
    def reportError(self, error, fatalError=False):
        print(f"ERROR: {error}")
        
    def pushInfo(self, info):
        print(f"INFO: {info}")
        
    def pushCommandInfo(self, info):
        print(f"COMMAND: {info}")
        
    def pushDebugInfo(self, info):
        print(f"DEBUG: {info}")

def check_postgis_connection(retry_count=0, max_retries=5, initial_delay=5):
    qgs = None
    try:
        # Basic system info
        print(f"Python Version: {platform.python_version()}")
        print(f"Python Implementation: {platform.python_implementation()}")
        print(f"System: {platform.system()} {platform.release()}")

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

        # Set the CRS in the URI
        uri.setSrid('2958')
        
        # Load as vector layer
        layer = QgsVectorLayer(uri.uri(False), "water_mains", "postgres")
        
        # Set the layer CRS explicitly
        layer.setCrs(QgsCoordinateReferenceSystem('EPSG:2958'))

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

def create_print_layout(layer, template_path="/app/map_templates/watermain_layout.qpt", output_path="/app/output/water_mains.pdf", retry_count=0, max_retries=3):
    """
    Create a print layout using water mains data from PostGIS.
    
    Args:
        layer (QgsVectorLayer): The PostGIS water mains layer
        template_path (str): Path to the template file
        output_path (str): Path where the PDF will be saved
        retry_count (int): Current retry attempt
        max_retries (int): Maximum number of retry attempts
    """
    try:
        # Get the layer's original CRS
        original_crs = layer.crs()
        print(f"Using original layer CRS: {original_crs.authid()}")
        
        # Comment out reprojection of water mains layer
        '''
        # Set target CRS to EPSG:2958
        target_crs = QgsCoordinateReferenceSystem('EPSG:2958')
        
        # Reproject water mains layer if needed
        if layer.crs() != target_crs:
            params = {
                'INPUT': layer,
                'TARGET_CRS': target_crs,
                'OUTPUT': 'memory:'  # Store in memory instead of file
            }
            feedback = PrintingFeedback()
            result = processing.run("native:reprojectlayer", params, feedback=feedback)
            layer = result['OUTPUT']
            QgsProject.instance().addMapLayer(layer)
            
            print("\n=== LAYER REPROJECTION ===")
            print("Layer successfully reprojected to:", layer.crs().authid())
            print("Reprojected layer feature count:", layer.featureCount())
            inspect_layer_features(layer)  # Call the inspection function for detailed output
        '''
        
        print(f"Layer CRS: {layer.crs().authid()}")

        # Configure basemap - use a basemap that works with the original CRS
        uri = (
            "type=xyz&"
            "url=https://abcd.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png&"
            "zmax=19&"
            "zmin=0&"
            "format=PNG"
        )

        # Create basemap layer
        basemap = QgsRasterLayer(uri, "CARTO Light", "wms")
        
        if not basemap.isValid():
            print(f"Failed to load basemap layer! Error: {basemap.error().message()}")
            return False
            
        # Comment out basemap reprojection
        '''
        # Reproject basemap
        params = {
            'INPUT': basemap,
            'TARGET_CRS': target_crs,
            'OUTPUT': 'memory:'
        }
        feedback = PrintingFeedback()
        result = processing.run("gdal:warpreproject", params, feedback=feedback)
        basemap = result['OUTPUT']
        '''
        
        QgsProject.instance().addMapLayer(basemap)
        
        # Verify layer is valid and has features
        if not layer.isValid():
            print("Layer is not valid!")
            return False
            
        feature_count = layer.featureCount()
        print(f"Layer contains {feature_count} features")
        
        # Style the layer
        style_water_mains(layer)
        
        # Create layout from template
        project = QgsProject.instance()
        manager = project.layoutManager()
        
        # Remove any existing layouts with the same name
        for layout in manager.layouts():
            if layout.name() == "Water Mains Layout":
                manager.removeLayout(layout)
        
        try:
            # Create a QDomDocument and load the template
            template_doc = QDomDocument()
            with open(template_path) as template_file:
                template_content = template_file.read()
                template_doc.setContent(template_content)
        except FileNotFoundError as e:
            print(f"Template file not found: {template_path}")
            return False
        
        layout = QgsPrintLayout(project)
        layout.loadFromTemplate(template_doc, QgsReadWriteContext())
        layout.setName("Water Mains Layout")
        
        # Add layout to manager
        manager.addLayout(layout)
        
        # Get the map item from template
        map_item = layout.itemById('Map 1')
        if not map_item:
            print("Could not find map item with id 'Map 1' in template")
            return False
            
        # Add our layers to the map (basemap first, then water mains)
        map_item.setLayers([basemap, layer])
        
        # Get the extent in the correct CRS
        extent = layer.extent()
        
        # Get the map item size ratio (width/height)
        map_width = map_item.sizeWithUnits().width()
        map_height = map_item.sizeWithUnits().height()
        frame_ratio = map_width / map_height
        
        # Get the layer extent ratio
        extent_width = extent.width()
        extent_height = extent.height()
        extent_ratio = extent_width / extent_height
        
        # Scale the extent to match the frame ratio while maintaining center
        if extent_ratio > frame_ratio:
            # Width is limiting factor, scale height to match
            new_height = extent_width / frame_ratio
            diff = new_height - extent_height
            extent.setYMinimum(extent.yMinimum() - diff/2)
            extent.setYMaximum(extent.yMaximum() + diff/2)
        else:
            # Height is limiting factor, scale width to match
            new_width = extent_height * frame_ratio
            diff = new_width - extent_width
            extent.setXMinimum(extent.xMinimum() - diff/2)
            extent.setXMaximum(extent.xMaximum() + diff/2)
            
        # Add padding (10%)
        extent.scale(1.1)
        
        # Set the extent to the map item
        map_item.setExtent(extent)
        
        # Refresh the map
        map_item.refresh()
        
        # Export to PDF
        print(f"Checking output path: {output_path}")
        print(f"Output directory exists: {os.path.exists(os.path.dirname(output_path))}")
        print(f"Output directory is writable: {os.access(os.path.dirname(output_path), os.W_OK)}")
        print(f"Full output path: {os.path.abspath(output_path)}")

        exporter = QgsLayoutExporter(layout)
        result = exporter.exportToPdf(output_path, QgsLayoutExporter.PdfExportSettings())
        
        if result == QgsLayoutExporter.Success:
            print(f"PDF exported successfully to: {output_path}")
            return True
        else:
            if retry_count < max_retries:
                print(f"PDF export failed. Retrying... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(5)
                return create_print_layout(layer, template_path, output_path, retry_count + 1, max_retries)
            else:
                print(f"PDF export failed with status: {result}")
                return False
            
    except Exception as e:
        if retry_count < max_retries:
            print(f"Error creating print layout: {str(e)}")
            print(f"Retrying... (Attempt {retry_count + 1}/{max_retries})")
            time.sleep(5)
            return create_print_layout(layer, template_path, output_path, retry_count + 1, max_retries)
        else:
            print(f"Max retries reached. Error: {str(e)}")
            return False

def style_water_mains(layer):
    """
    Style the water mains layer based on attributes from the database.
    """
    # Create a categorized renderer based on material type
    field_name = 'material'  # from your database
    categories = []
    
    # Define colors for different materials
    material_colors = {
        'PVC': '#FF0000',
        'STEEL': '#0000FF',
        'IRON': '#00FF00',
        'COPPER': '#FFA500',
        'OTHER': '#808080'
    }
    
    # Create category for each material type
    for material, color in material_colors.items():
        symbol = QgsLineSymbol.createSimple({
            'line_color': color,
            'line_width': '0.7'
        })
        category = QgsRendererCategory(material, symbol, material)
        categories.append(category)
    
    renderer = QgsCategorizedSymbolRenderer(field_name, categories)
    layer.setRenderer(renderer)
    
    # Add labels if needed
    label_settings = QgsPalLayerSettings()
    label_settings.fieldName = 'pipe_size'  # or any other field you want to show
    label_settings.enabled = True
    
    layer_settings = QgsVectorLayerSimpleLabeling(label_settings)
    layer.setLabeling(layer_settings)
    layer.setLabelsEnabled(True)

def load_water_mains_layer(retry_count=0, max_retries=5, delay=5):
    """
    Load water mains layer from PostGIS database with retry logic.
    
    Args:
        retry_count (int): Current retry attempt
        max_retries (int): Maximum number of retry attempts
        delay (int): Delay in seconds between retries
    """
    try:
        # Set up the PostGIS connection
        uri = QgsDataSourceUri()
        uri.setConnection(
            "postgis-db-service",  # host
            "5432",                # port
            "gis_data",           # database name
            "gis_user",           # username
            "password"            # password
        )
        
        # Set up the layer details
        uri.setDataSource(
            "public",       # schema
            "water_mains",  # table
            "geometry",     # geometry column
            "",            # SQL WHERE clause
            "id"           # Primary key
        )
        
        # Create and load the layer
        layer = QgsVectorLayer(uri.uri(), "Water Mains", "postgres")
        
        if not layer.isValid():
            if retry_count < max_retries:
                print(f"Layer failed to load! Retrying in {delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(delay)
                return load_water_mains_layer(retry_count + 1, max_retries, min(delay * 2, 60))
            else:
                print("Max retries reached. Failed to load layer.")
                return None
        
        # Check if layer has features
        feature_count = layer.featureCount()
        if feature_count == 0:
            if retry_count < max_retries:
                print(f"Layer loaded but contains no features! Retrying in {delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(delay)
                return load_water_mains_layer(retry_count + 1, max_retries, min(delay * 2, 60))
            else:
                print("Max retries reached. No features found in layer.")
                return None
        
        # Add layer to the project
        QgsProject.instance().addMapLayer(layer)
        
        # Add diagnostic information
        print("Successfully added layer to the project!")
        print(f"Feature count: {feature_count}")
        print(f"Layer CRS: {layer.crs().authid()}")
        print(f"Layer fields: {[field.name() for field in layer.fields()]}")
        
        return layer
        
    except Exception as e:
        if retry_count < max_retries:
            print(f"Error loading layer: {str(e)}")
            print(f"Retrying in {delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
            time.sleep(delay)
            return load_water_mains_layer(retry_count + 1, max_retries, min(delay * 2, 60))
        else:
            print(f"Max retries reached. Error: {str(e)}")
            return None

if __name__ == "__main__":
    try:
        # Load the water mains layer with retry logic
        layer = load_water_mains_layer()
        if layer:
            # Set project CRS to match layer CRS instead of forcing EPSG:2958
            project = QgsProject.instance()
            project.setCrs(layer.crs())
            
            # Inspect some features (optional)
            inspect_layer_features(layer)
            
            # Create the PDF with retry logic
            create_print_layout(layer)
    finally:
        # Clean up
        qgs.exitQgis()

# if __name__ == "__main__":
#     try:
#         # Set project CRS
#         project = QgsProject.instance()
#         project.setCrs(QgsCoordinateReferenceSystem('EPSG:2958'))
        
#         # Load the water mains layer with retry logic
#         layer = load_water_mains_layer()
#         if layer:
#             # Inspect some features (optional)
#             inspect_layer_features(layer)
            
#             # Create the PDF with retry logic
#             create_print_layout(layer)
#     finally:
#         # Clean up
#         qgs.exitQgis()

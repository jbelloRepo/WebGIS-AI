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
    QgsProcessingFeedback,
    QgsFeature
)
from qgis.PyQt.QtXml import QDomDocument
import os

# Initialize QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:2958"))


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

def create_print_layout(layer, template_path="/app/map_templates/watermain_layout_1.qpt", output_path="/app/output/water_mains.pdf", retry_count=0, max_retries=3):
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
        print(f"===== def create_print_layout() ===== Layer CRS: {original_crs.authid()}")
        
        print(f"Layer CRS: {layer.crs().authid()}")

        # Configure basemap - use OpenStreetMap
        uri = (
            "type=xyz&"
            "url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&"
            "zmax=19&"
            "zmin=0&"
            "format=PNG"
        )

        # Create basemap layer
        basemap = QgsRasterLayer(uri, "OpenStreetMap", "wms")
        
        if not basemap.isValid():
            print(f"Failed to load basemap layer! Error: {basemap.error().message()}")
            return False
            
        # Reproject basemap to match the vector layer's CRS if needed
        if basemap.crs().authid() != layer.crs().authid():
            print(f"Basemap CRS ({basemap.crs().authid()}) differs from layer CRS ({layer.crs().authid()})")
            print("Reprojecting basemap to match layer CRS")
            reprojected_basemap = reproject_raster_layer(basemap, layer.crs().authid())
            if reprojected_basemap:
                basemap = reprojected_basemap
            else:
                print("Warning: Basemap reprojection failed, using original basemap")
        
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
        map_item.setLayers([layer, basemap])
        
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
            'line_width': '0.3'
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

def reproject_layer(layer, target_crs_string, transform_context=None):
    """
    Reproject a QGIS vector layer to a different coordinate reference system.
    
    Args:
        layer (QgsVectorLayer): The layer to reproject
        target_crs_string (str): The target CRS as a string (e.g., 'EPSG:4326')
        transform_context (QgsCoordinateTransformContext, optional): Transform context for advanced transformations
    
    Returns:
        QgsVectorLayer: The reprojected layer
    """
    try:
        print("\n=== LAYER REPROJECTION STARTED ===")
        print(f"Source layer: {layer.name()}")
        print(f"Feature count: {layer.featureCount()}")
        
        # Create target CRS object
        target_crs = QgsCoordinateReferenceSystem(target_crs_string)
        
        if not target_crs.isValid():
            print(f"Error: Invalid target CRS: {target_crs_string}")
            return None
            
        # Get the source CRS
        source_crs = layer.crs()
        print(f"Source CRS: {source_crs.authid()} - {source_crs.description()}")
        print(f"Target CRS: {target_crs.authid()} - {target_crs.description()}")
        
        # If the layer is already in the target CRS, return it as is
        if source_crs == target_crs:
            print(f"Layer already in target CRS: {target_crs_string} - No reprojection needed")
            return layer
            
        # Create a new layer name
        new_layer_name = f"{layer.name()} ({target_crs_string})"
        print(f"Creating new layer: {new_layer_name}")
        
        # Get the transform context if not provided
        if transform_context is None:
            print("Using project transform context")
            transform_context = QgsProject.instance().transformContext()
        else:
            print("Using provided transform context")
        
        # Create the coordinate transform
        transform = QgsCoordinateTransform(source_crs, target_crs, transform_context)
        print(f"Transform created: {source_crs.authid()} → {target_crs.authid()}")
        
        # Use processing algorithm instead of manual feature copying
        print("Using processing algorithm for reprojection")
        params = {
            'INPUT': layer,
            'TARGET_CRS': target_crs,
            'OUTPUT': 'memory:'  # Store in memory instead of file
        }
        feedback = PrintingFeedback()
        result = processing.run("native:reprojectlayer", params, feedback=feedback)
        new_layer = result['OUTPUT']
        
        # Verify the new layer
        print(f"Reprojection complete. New layer has {new_layer.featureCount()} features")
        print(f"New layer CRS: {new_layer.crs().authid()}")
        
        # Check for any feature loss
        if new_layer.featureCount() != layer.featureCount():
            print(f"Warning: Feature count mismatch! Original: {layer.featureCount()}, New: {new_layer.featureCount()}")
        
        # Set the layer name
        new_layer.setName(new_layer_name)
        
        print("=== LAYER REPROJECTION COMPLETED ===\n")
        return new_layer
        
    except Exception as e:
        print(f"Error reprojecting layer: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def reproject_raster_layer(layer, target_crs_string, transform_context=None):
    """
    Reproject a QGIS raster layer to a different coordinate reference system.
    
    Args:
        layer (QgsRasterLayer): The raster layer to reproject
        target_crs_string (str): The target CRS as a string (e.g., 'EPSG:4326')
        transform_context (QgsCoordinateTransformContext, optional): Transform context for advanced transformations
    
    Returns:
        QgsRasterLayer: The reprojected raster layer
    """
    try:
        print("\n=== RASTER LAYER REPROJECTION STARTED ===")
        print(f"Source layer: {layer.name()}")
        
        # Create target CRS object
        target_crs = QgsCoordinateReferenceSystem(target_crs_string)
        
        if not target_crs.isValid():
            print(f"Error: Invalid target CRS: {target_crs_string}")
            return None
            
        # Get the source CRS
        source_crs = layer.crs()
        print(f"Source CRS: {source_crs.authid()} - {source_crs.description()}")
        print(f"Target CRS: {target_crs.authid()} - {target_crs.description()}")
        
        # If the layer is already in the target CRS, return it as is
        if source_crs == target_crs:
            print(f"Layer already in target CRS: {target_crs_string} - No reprojection needed")
            return layer
            
        # Create a new layer name
        new_layer_name = f"{layer.name()} ({target_crs_string})"
        print(f"Creating new layer: {new_layer_name}")
        
        # For XYZ tile services, we need a different approach
        if layer.providerType() == 'wms' and 'type=xyz' in layer.source():
            print("Detected XYZ tile service - using on-the-fly reprojection")
            
            # For XYZ services, we'll create a new layer with the same source
            # but set the desired CRS and let QGIS handle the reprojection
            new_layer = QgsRasterLayer(layer.source(), new_layer_name, 'wms')
            
            if new_layer.isValid():
                # Set the CRS explicitly
                new_layer.setCrs(target_crs)
                print(f"Created new XYZ layer with target CRS: {target_crs.authid()}")
                print("=== RASTER LAYER REPROJECTION COMPLETED ===\n")
                return new_layer
            else:
                print(f"Failed to create new XYZ layer: {new_layer.error().message()}")
                print("Returning original layer")
                return layer
        
        # For regular raster layers, use GDAL warp
        try:
            print("Using GDAL warp algorithm for raster reprojection")
            params = {
                'INPUT': layer,
                'SOURCE_CRS': source_crs,
                'TARGET_CRS': target_crs,
                'RESAMPLING': 1,  # 0=nearest neighbor, 1=bilinear, 2=cubic, etc.
                'NODATA': None,   # Leave as is
                'TARGET_RESOLUTION': None,  # Use input resolution
                'OPTIONS': '',
                'DATA_TYPE': 0,   # Use input data type
                'TARGET_EXTENT': None,  # Calculate automatically
                'TARGET_EXTENT_CRS': None,
                'MULTITHREADING': True,
                'EXTRA': '',
                'OUTPUT': 'memory:'  # Store in memory instead of file
            }
            
            feedback = PrintingFeedback()
            result = processing.run("gdal:warpreproject", params, feedback=feedback)
            new_layer = result['OUTPUT']
            
            # Verify the new layer
            print(f"Reprojection complete. New layer CRS: {new_layer.crs().authid()}")
            
            # Set the layer name
            new_layer.setName(new_layer_name)
            
            print("=== RASTER LAYER REPROJECTION COMPLETED ===\n")
            return new_layer
        except Exception as gdal_error:
            print(f"GDAL warp failed: {str(gdal_error)}")
            print("Returning original layer")
            return layer
        
    except Exception as e:
        print(f"Error reprojecting raster layer: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return layer  # Return the original layer instead of None

if __name__ == "__main__":
    try:
        # Load the water mains layer with retry logic
        layer = load_water_mains_layer()
        if layer:
            # Reproject the layer to EPSG:2958 if needed
            if layer.crs().authid() != 'EPSG:2958':
                reprojected_layer = reproject_layer(layer, 'EPSG:2958')
                if reprojected_layer:
                    # Remove the original layer
                    QgsProject.instance().removeMapLayer(layer.id())
                    # Add the reprojected layer to the project
                    QgsProject.instance().addMapLayer(reprojected_layer)
                    # Use the reprojected layer for further operations
                    layer = reprojected_layer
            
            # Set project CRS to match layer CRS
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

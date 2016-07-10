import bpy
import bmesh
from math import *
from mathutils import *
from bpy.props import *
import bmesh
import math
import mathutils
import time
import json
import os
from bpy_extras.io_utils import ImportHelper, ExportHelper

class dmh_options():
    """class to save the AddOn-options

    """ 
    # Define and initalize variables
    LIST_VERT = []
    LIST_FACE = []
    LIST_EDGE_CONNECT = [[]]

    DEFAULT_KNOT_TYPE = "UV"
    DEFAULT_VERTEX_PVR = False
    DEFAULT_EDGE_PVR = False
    DEFAULT_HIDE_KNOTS = False
    DEFAULT_KNOT_RADIUS = 0.1
    DEFAULT_KNOT_RESOLUTION = 8
    DEFAULT_EDGE_RADIUS = 0.03
    DEFAULT_EDGE_RESOLUTION = 6
    DEFAULT_SMOOTH = False
    DEFAULT_IMPORT = False
    DEFAULT_ACTUAL_STATE = "NEW"
    IMPORT_DATA = []
    IMPORT_knot_type = "UV"
    IMPORT_VERTEX_PVR = False
    IMPORT_EDGE_PVR = False
    IMPORT_HIDE_KNOTS = False
    IMPORT_KNOT_RADIUS = 0.1
    IMPORT_KNOT_RESOLUTION = 8
    IMPORT_EDGE_RADIUS = 0.03
    IMPORT_EDGE_RESOLUTION = 6
    IMPORT_SMOOTH = False

    def __init__(self):
        print("Inititalising dmh_options...")
    
    # setter function    
    def set_import(self,
                   import_data,
                   import_knot_type,
                   import_vertex_pvr,
                   import_edge_pvr,
                   import_hide_knots,
                   import_knot_resolution,
                   import_knot_radius,
                   import_edge_resolution,
                   import_edge_radius,
                   import_smooth
                   ):
        self.IMPORT_DATA = import_data
        self.IMPORT_knot_type = import_knot_type
        self.IMPORT_VERTEX_PVR = import_vertex_pvr
        self.IMPORT_EDGE_PVR = import_edge_pvr
        self.IMPORT_HIDE_KNOTS = import_hide_knots
        self.IMPORT_KNOT_RESOLUTION = import_knot_resolution
        self.IMPORT_KNOT_RADIUS = import_knot_radius
        self.IMPORT_EDGE_RESOLUTION = import_edge_resolution
        self.IMPORT_EDGE_RADIUS = import_edge_radius
        self.IMPORT_SMOOTH = import_smooth
        
def import_data(fileName):
    """import data from a '.dmh'-File

    :param fileName: Path and name of file 
    :type fileName: str. 

    :returns: none -- importing data and saving them in bpy.types.Scene.dmh 

    """ 
    options = bpy.types.Scene.dmh

    # open file and load data
    f = open(fileName,'r')
    data_load = json.load(f)
    data = data_load[0]
    
    # store data in options
    options.set_import([data[0],data[1],data[2],data[3]],
                                   data[4],
                                   data[5],
                                   data[6],
                                   data[7],
                                   data[8],
                                   data[9],
                                   data[10],
                                   data[11],
                                   data[12]
                                   )  
    
    # create model and change state
    options.DEFAULT_ACTUAL_STATE = "IMPORT"
    bpy.ops.mesh.dmh_add()
    options.DEFAULT_ACTUAL_STATE = "NEW"

def export_data(fileName):
    """export data to a '.dmh'-File

    :param fileName: Path and name of file 
    :type fileName: str. 
    :returns: none -- exporting all data stored in bpy.types.Scene.dmh to file in json format

    """ 
    options = bpy.types.Scene.dmh
    
    # open file and store date
    f = open(fileName,'w')
    
    list_vertices = []
    for v in options.data[0]:
        list_vertices.append([v[0],v[1],v[2]])    
    
    world_pos = [options.data[2][0][3], options.data[2][1][3], options.data[2][2][3]]
      
    wireframe = [
                list_vertices, 
                options.data[1], world_pos, options.data[3],
                options.knot_type,
                options.vertex_pvr,
                options.edge_pvr,
                options.hide_knots,
                options.knot_resolution,
                options.knot_radius,
                options.edge_resolution,
                options.edge_radius,
                options.smooth
                ]

    data = [wireframe]
    json.dump(data, f)

def make_obj():
    """creating an object by using all data stored in options

    :returns: none -- exporting all data stored in bpy.types.Scene.dmh to file in json format

    """ 
    options = bpy.types.Scene.dmh
    data = options.data  

    # For the end points add the original knot vertice to list for correct modelling in case that the knots should be hided    
    for i in range(0,len(options.LIST_EDGE_CONNECT)):
        if len(options.LIST_EDGE_CONNECT[i]) == options.edge_resolution:
            vec_v = data[2]*data[0][i]
            options.LIST_VERT.append((vec_v.x,vec_v.y,vec_v.z))
            options.LIST_EDGE_CONNECT[i].append(len(options.LIST_VERT)-1)

    # in case of edge_pvr scale ends of edges
    if options.edge_pvr:
        for i in range(0,len(options.LIST_EDGE_CONNECT)):
            if data[3][i] < 0.1:
                factor = 0.9
            else:
                factor = 1 - data[3][i]
            for x in range(0,len(options.LIST_EDGE_CONNECT[i])):
                transl = Vector(data[2]*data[0][i]) - Vector(options.LIST_VERT[options.LIST_EDGE_CONNECT[i][x]])
                transl = Vector((transl.x*factor,transl.y*factor,transl.z*factor)) 
                new_vec = Vector(options.LIST_VERT[options.LIST_EDGE_CONNECT[i][x]]) + transl
                options.LIST_VERT[options.LIST_EDGE_CONNECT[i][x]] = (new_vec.x,new_vec.y,new_vec.z) 

    # creating object
    print("Vertices: ", len(options.LIST_VERT))
    print("Faces: ", len(options.LIST_FACE))
    dmh_mesh = bpy.data.meshes.new('dmh')
    dmh_mesh.from_pydata(options.LIST_VERT, [], options.LIST_FACE)

    bm = bmesh.new()
    bm.from_mesh(dmh_mesh)
    bm.verts.ensure_lookup_table()

    # connecting edges
    for i in range(0,len(options.LIST_EDGE_CONNECT)):
        if len(options.LIST_EDGE_CONNECT[i]) > 3:
            if (data[3][i] == 0.0):
                bmesh.ops.convex_hull(bm,input=[bm.verts[d] for d in options.LIST_EDGE_CONNECT[i]])    
    bm.to_mesh(dmh_mesh)
    
    # finish object creating and choose shading
    bm.free
    dmh_obj = bpy.data.objects.new("DMH", dmh_mesh)
    bpy.context.scene.objects.link(dmh_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = bpy.data.objects[dmh_obj.name]
    bpy.data.objects[dmh_obj.name].select = True
    if (options.smooth):
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()

def main_function(context):
    """main function of the AddOn

    :returns: 'FINISHED'

    """ 

    # Debug Info
    zeit = time.time()
    print("Modelling Hull")     

    options = bpy.types.Scene.dmh  

    del options.LIST_VERT[:]
    del options.LIST_FACE[:]
    del options.LIST_EDGE_CONNECT[:]

    # Creating knots and edges
    
    createEdges(options.data, options.edge_pvr, options.knot_radius, options.edge_radius, options.edge_resolution)
    createKnots(options.data, options.knot_type, options.vertex_pvr, options.hide_knots, options.knot_radius, options.knot_resolution)

    make_obj()

    # Debug Info
    print("Finished in ", time.time() - zeit, " seconds.\n")
        
    return {'FINISHED'}

def copyBmesh(src, sca, rot, loc):
    """copying vertices' coordinates and faces from a source Bmesh to AddOn options

    :param src: source Bmesh that will be copied 
    :type src: bmesh
    :param sca: scaling matrix that will be used for transformation of the source Bmesh  
    :type sca: 4x4-matrix
    :param rot: rotation matrix that will be used for transformation of the source Bmesh  
    :type rot: 4x4-matrix
    :param loc: translationn vector that will be used for transformation of the source Bmesh  
    :type loc: 4D-vector
    :param src: source Bmesh that will be copied 
    :type src: bmesh
    :returns: none -- exporting all data stored in bpy.types.Scene.dmh to file in json format

    """ 
    options = bpy.types.Scene.dmh
    source = src.copy()
    start_index = len(options.LIST_VERT)
    
    # transform
    source.transform(matrix=sca)
    m = loc * rot
    source.transform(matrix=m)

    # copying data
    for v in source.verts:
        options.LIST_VERT.append((v.co.x,v.co.y,v.co.z))
    for f in source.faces:
        if len(f.verts) == 3:
            options.LIST_FACE.append([f.verts[0].index+start_index,f.verts[1].index+start_index,f.verts[2].index+start_index])
        elif len(f.verts) == 4:
            options.LIST_FACE.append([f.verts[0].index+start_index,f.verts[1].index+start_index,f.verts[2].index+start_index,f.verts[3].index+start_index])


# Function to create the hull for knots of a input object/tree
# createKnots( 
#               input object/tree,
#               target bMesh
#               )
def createKnots(data, knot_type, vertex_pvr, hide_knots, radius, knot_resolution):
    """modelling knots

    :param src: source Bmesh that will be copied 
    :type src: bmesh
    :param sca: scaling matrix that will be used for transformation of the source Bmesh  
    :type sca: 4x4-matrix
    :param rot: rotation matrix that will be used for transformation of the source Bmesh  
    :type rot: 4x4-matrix
    :param loc: translationn vector that will be used for transformation of the source Bmesh  
    :type loc: 4D-vector
    :param src: source Bmesh that will be copied 
    :type src: bmesh
    :returns: none -- exporting all data stored in bpy.types.Scene.dmh to file in json format

    """ 

    # get world matrix and list of vertices of input object  
    om = data[2]
    listVertices = data[0]

    # Debug Info
    print("Starting to create ",len(listVertices) , " bMesh Knots")
    print("Knot-Type: ", knot_type)
    
    # Create one model bMesh for knots        
    src = bmesh.new()
    if (knot_type=="UV"):
        bmesh.ops.create_uvsphere(src, u_segments = knot_resolution, v_segments = knot_resolution, diameter = radius)
    elif (knot_type=="ICO"):
        bmesh.ops.create_icosphere(src, subdivisions = knot_resolution, diameter = radius)
    elif (knot_type=="CUBE"):
        bmesh.ops.create_cube(src, size = radius*2)

    # Debug Info
    counter = 0    

    # For every knot    
    for i in range(0, len(listVertices)):
        counter += 1
        if (not (hide_knots and (len(bpy.types.Scene.dmh.LIST_EDGE_CONNECT[i]) == bpy.types.Scene.dmh.edge_resolution * 2))):
            if (vertex_pvr):
                bw = data[3][i]
            else:
                bw = 1.0
            if (bw != 0.0):
                lc = listVertices[i]
                v = om * lc
                # Scaling matrix
                sca = Matrix.Scale(1.0*bw, 4, (0.0, 0.0, 1.0)) * Matrix.Scale(1.0*bw, 4, (0.0, 1.0, 0.0)) * Matrix.Scale(1.0*bw, 4, (1.0, 0.0, 0.0))
                # Rotation matrix
                rot = Euler((0.0, 0.0, 0.0)).to_matrix().to_4x4()
                # Translation matrix
                loc = Matrix.Translation(v)
                # Copy model bMesh to target bMesh
                copyBmesh(src, sca, rot, loc)

    # Free memory
    src.free()
   
def createEdges(data, edge_pvr, knot_radius, edge_radius, edge_resolution):
    """modelling knots

    :param data: list of verticed, edges, world matrix and bevel weights 
    :type data: list
    :param edge_pvr: option to use edge Pro-Vertex-Radius  
    :type edge_pvr: boolean
    :param knot_radius: radius for the knots  
    :type knot_radius: float
    :param edge_radius: radius for the edges  
    :type edge_radius: float
    :param edge_resolution: resolution for the edges
    :type edge_resolution: integer
    :returns: none -- calling copyBmesh()

    """ 

    options = bpy.types.Scene.dmh 

    # transform input object/tree into bmesh
    om = data[2]
       
    # Create one model bMesh for edges
    src = bmesh.new()
    bmesh.ops.create_cone(src, segments=edge_resolution, diameter1=edge_radius, diameter2=edge_radius, depth=1.0)

    # For every knot 
    for edge in data[1]:
        
        # Get coordinates of vertices of the edge
        vecA = om * data[0][edge[0]]
        vecB = om * data[0][edge[1]]

        # If the two vertices are not equal
        if ((vecA - vecB).length > 0):

            # calculate the distance between the two vertices            
            if knot_radius-edge_radius < 2*edge_radius:
                dist = ((vecB) - (vecA)).length - (knot_radius-edge_radius)
            else:
                dist = ((vecB) - (vecA)).length - (2*edge_radius)

            # calculate the middlepoint coordinates
            xLength = vecB[0] - vecA[0]
            yLength = vecB[1] - vecA[1]
            zLength = vecB[2] - vecA[2]
            location = Vector((xLength/2 + vecA[0], yLength/2 + vecA[1], zLength/2 + vecA[2]))

            # calculate the angles to rotate the model bMesh into position
            phi = atan2(yLength, xLength) 
            help = zLength/(vecB - vecA).length
            if (help < -1.0): # making sure that acos is used in range of -1.0 to 1.0
                help = -1.0
            elif (help > 1.0):
                help = 1.0
            theta = acos(help)

            # Scaling matrix             
            sca = Matrix.Scale(dist, 4, (0.0, 0.0, 1.0)) * Matrix.Scale(1.0, 4, (0.0, 1.0, 0.0)) * Matrix.Scale(1.0, 4, (1.0, 0.0, 0.0))
            # Rotation matrix  
            rot = mathutils.Euler((0.0, theta, phi)).to_matrix().to_4x4()
            # Translation matrix  
            loc = Matrix.Translation(location)
            # Copy model bMesh to target bMesh        
            copyBmesh(src, sca, rot, loc)

            # Allocate vertices to the knot that they belong to
            while ((len(options.LIST_EDGE_CONNECT)-1 < edge[0]) or (len(options.LIST_EDGE_CONNECT)-1 < edge[1])):
                options.LIST_EDGE_CONNECT.append([])          

            for i in range(len(options.LIST_VERT)-(2*edge_resolution),len(options.LIST_VERT)):
                if (Vector(options.LIST_VERT[i])-vecA).length < (Vector(options.LIST_VERT[i])-vecB).length:
                    options.LIST_EDGE_CONNECT[edge[0]].append(i)
                else:
                    options.LIST_EDGE_CONNECT[edge[1]].append(i)

    # free memory		    
    src.free()



class dmh_add(bpy.types.Operator):
    """Operator class (bpy.types.Operator)

    :returns: 'FINISHED'

    """ 
    '''Add a Wireframe Cover'''
    bl_idname = "mesh.dmh_add"
    bl_label = "Add a Wireframe Cover"
    bl_options = {'REGISTER', 'UNDO'}

    bpy.types.Scene.dmh = dmh_options()
 
    knot_types = [
    ("ICO", "Ico-Sphere", "", 1),
    ("UV", "UV-Sphere", "", 2),
    ("CUBE", "Cube", "", 3),
    ]

    # taking care of right resolutions for every knot type
    def update_knot_type(self, context):
        if self.knot_type == "ICO":
            self.knot_resolution = 2
        elif self.knot_type == "CUBE":
            self.knot_resolution = 0
        elif self.knot_type == "UV":
            self.knot_resolution = 8

    # taking care of right resolutions for every knot type
    def update_knot_resolution(self, context):
        min = 0
        print(self)
        if self.knot_type == "ICO":
            min = 1
        elif self.knot_type == "CUBE":
            self.knot_resolution = 0
        elif self.knot_type == "UV":
            min = 3
        if self.knot_resolution < min:
            self.knot_resolution = min

    # taking care of minimum knot radius
    def update_knot_radius(self,context):
        if self.knot_radius < self.edge_radius*1.25:
            self.knot_radius=self.edge_radius*1.25

    # taking care of maximum edge radius
    def update_edge_radius(self,context):
        if self.edge_radius > self.knot_radius*0.8:
            self.edge_radius=self.knot_radius*0.8

    options = bpy.types.Scene.dmh 

    # creating properties
    knot_type = EnumProperty(items=knot_types, default=options.DEFAULT_KNOT_TYPE, name="Knot-Type", update=update_knot_type)
    vertex_pvr = BoolProperty(name="Knot PVR", default=options.DEFAULT_VERTEX_PVR)
    edge_pvr = BoolProperty(name="Edge PVR", default=options.DEFAULT_EDGE_PVR)
    hide_knots = BoolProperty(name="Hide knots with 2 edges", default=options.DEFAULT_HIDE_KNOTS)
    knot_radius = FloatProperty(name="Knot-Radius", default=options.DEFAULT_KNOT_RADIUS, min=0.001, max=100.0,update=update_knot_radius)
    knot_resolution = IntProperty(name="Knot-Resolution", default=options.DEFAULT_KNOT_RESOLUTION, min=0, max=128, update=update_knot_resolution)
    edge_radius = FloatProperty(name="Edge-Radius", default=options.DEFAULT_EDGE_RADIUS, min=0.001, max=100.0,update=update_edge_radius)
    edge_resolution = IntProperty(name="Edge-Resolution", default=options.DEFAULT_EDGE_RESOLUTION, min=3, max=128)
    smooth = BoolProperty(name="Smooth-Shading", default=options.DEFAULT_SMOOTH)
      
    def execute(self, context):
        
        options = bpy.types.Scene.dmh 
        
        ACTUAL_STATE = options.DEFAULT_ACTUAL_STATE      
        
        # load default values when creating new dmh
        if (ACTUAL_STATE == "NEW"):
            self.knot_type = options.DEFAULT_KNOT_TYPE
            self.vertex_pvr = options.DEFAULT_VERTEX_PVR
            self.edge_pvr = options.DEFAULT_EDGE_PVR
            self.hide_knots = options.DEFAULT_HIDE_KNOTS
            self.knot_radius = options.DEFAULT_KNOT_RADIUS
            self.knot_resolution = options.DEFAULT_KNOT_RESOLUTION
            self.edge_radius = options.DEFAULT_EDGE_RADIUS
            self.edge_resolution = options.DEFAULT_EDGE_RESOLUTION
            self.smooth = options.DEFAULT_SMOOTH

        # load default values when importing dmh
        if (ACTUAL_STATE == "IMPORT"):        
            self.knot_type = options.IMPORT_knot_type
            self.vertex_pvr = options.IMPORT_VERTEX_PVR
            self.edge_pvr = options.IMPORT_EDGE_PVR
            self.hide_knots = options.IMPORT_HIDE_KNOTS
            self.knot_radius = options.IMPORT_KNOT_RADIUS
            self.knot_resolution = options.IMPORT_KNOT_RESOLUTION
            self.edge_radius = options.IMPORT_EDGE_RADIUS
            self.edge_resolution = options.IMPORT_EDGE_RESOLUTION
            self.smooth = options.IMPORT_SMOOTH
            
            # creating wireframe from imported data 
            dmh_tree_mesh = bpy.data.meshes.new('dmh_tree')
            dmh_tree_mesh.from_pydata(options.IMPORT_DATA[0], options.IMPORT_DATA[1], [])
            dmh_tree_obj = bpy.data.objects.new("DMH-TREE", dmh_tree_mesh)
            bpy.context.scene.objects.link(dmh_tree_obj)
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = bpy.data.objects[dmh_tree_obj.name]
            bpy.data.objects[dmh_tree_obj.name].select = True
            bpy.ops.transform.translate(value=options.IMPORT_DATA[2])
            for i in range(0, len(options.IMPORT_DATA[3])):
                bpy.context.selected_objects[0].data.vertices[i].bevel_weight = options.IMPORT_DATA[3][i]
                
        if (len(bpy.context.selected_objects)==1):
            
            options.DEFAULT_ACTUAL_STATE ="RUN"
            ACTUAL_STATE == "RUN" 
            obj = bpy.context.selected_objects[0]

            # loading data
            om = obj.matrix_world
            v = [vec.co for vec in obj.data.vertices]
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            e = []
            for edge in bm.edges:
                e.append([edge.verts[0].index, edge.verts[1].index])
            bw = [vec.bevel_weight for vec in obj.data.vertices]
            data = [v,e,om,bw]

            # setting options
            options.knot_type = self.knot_type
            options.vertex_pvr = self.vertex_pvr
            options.edge_pvr = self.edge_pvr
            options.hide_knots = self.hide_knots
            options.knot_resolution = self.knot_resolution
            options.knot_radius = self.knot_radius
            options.edge_resolution = self.edge_resolution
            options.edge_radius = self.edge_radius
            options.smooth = self.smooth
            options.data = data
            
            # execute main function
            new_obj = main_function(context)
            
        else:
            self.report({'INFO'}, 'No active object or to many selected objects.')
        return {'FINISHED'}
 
def menu_func(self, context):
    """Menu function

    :returns: none

    """ 

    self.layout.operator("mesh.dmh_add", 
        text="Wireframe Cover", 
        icon='OUTLINER_OB_EMPTY')

class DMHImport(bpy.types.Operator, ImportHelper):
    """Operator class (bpy.types.Operator, ImportHelper)

    :returns: 'FINISHED'

    """ 
    bl_idname = "i.dmh"
    bl_label = "Import DMH"

    def execute(self, context):
        path = "Importing " + self.properties.filepath
        self.report({'INFO'}, path)
        import_data(self.properties.filepath)
        return{'FINISHED'}

class DMHExport(bpy.types.Operator, ExportHelper):
    """Operator class (bpy.types.Operator, ExportHelper)

    :returns: 'FINISHED'

    """     
    bl_idname = "e.dmh"
    bl_label = "Export DMH"

    filename_ext = ".dmh"
    filter_glob = StringProperty(default="*.dmh", options={'HIDDEN'})

    def execute(self, context):
        path = "Exporting " + self.properties.filepath
        self.report({'INFO'}, path)
        export_data(self.properties.filepath)
        return{'FINISHED'}

def menu_func_import(self, context):
    """Menu function

    :returns: none

    """ 
    self.layout.operator(
        DMHImport.bl_idname, text="DMH (.dmh)")

def menu_func_export(self, context):
    """Menu function

    :returns: none

    """ 
    self.layout.operator(
        DMHExport.bl_idname, text="DMH (.dmh)")

# registering functions and classes to blender
def register():
   bpy.utils.register_module(__name__)
   bpy.types.INFO_MT_add.prepend(menu_func)
   bpy.types.INFO_MT_file_import.append(menu_func_import)
   bpy.types.INFO_MT_file_export.append(menu_func_export)

# unregistering functions and classes from blender 
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_add.remove(menu_func)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()

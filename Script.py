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

LIST_VERT = []
LIST_FACE = []
LIST_EDGE_CONNECT = [[]]

DEFAULT_TYPE_K = "UV"
DEFAULT_PRO_V = False
DEFAULT_PRO_E = False
DEFAULT_RADIUS_K = 0.1
DEFAULT_RES_K = 8
DEFAULT_RADIUS_E = 0.03
DEFAULT_RES_E = 6
DEFAULT_SMOOTH = False
DEFAULT_IMPORT = False
IMPORT_TYPE_K = "UV"
IMPORT_PRO_V = False
IMPORT_PRO_E = False
IMPORT_RADIUS_K = 0.1
IMPORT_RES_K = 8
IMPORT_RADIUS_E = 0.03
IMPORT_RES_E = 6
IMPORT_SMOOTH = False
IMPORT_DATA = []

state = [
    ("NEW", "New", "", 1),
    ("IMPORT", "Import", "", 2),
    ("RUN", "Run", "", 3),
    ]

DEFAULT_ACTUAL_STATE = "NEW"

def load_data(fileName):
    f = open(fileName,'r')
    data_load = json.load(f)
    data = data_load[0]
    
    global DEFAULT_ACTUAL_STATE
    global IMPORT_DATA
    global IMPORT_TYPE_K
    global IMPORT_PRO_V
    global IMPORT_PRO_E
    global IMPORT_RES_K
    global IMPORT_RADIUS_K
    global IMPORT_RES_E
    global IMPORT_RADIUS_E
    global IMPORT_SMOOTH

    IMPORT_DATA = [data[0],data[1],data[2],data[3]]    
    IMPORT_TYPE_K = data[4]
    IMPORT_PRO_V = data[5]
    IMPORT_PRO_E = data[6]
    IMPORT_RES_K = data[7]
    IMPORT_RADIUS_K = data[8]
    IMPORT_RES_E = data[9]
    IMPORT_RADIUS_E = data[10]
    IMPORT_SMOOTH = data[11]    
    
    DEFAULT_ACTUAL_STATE = "IMPORT"
    bpy.ops.mesh.dmh_add()
    DEFAULT_ACTUAL_STATE = "NEW"

def save_data(fileName):
    f = open(fileName,'w')
    
    list_vertices = []
    for v in bpy.types.Scene.data[0]:
        list_vertices.append([v[0],v[1],v[2]]) 
        
    options = bpy.types.Scene    
    
    world_pos = [options.data[2][0][3], options.data[2][1][3], options.data[2][2][3]]
      
    wireframe = [
                list_vertices, 
                options.data[1], world_pos, options.data[3],
                options.type_k,
                options.pro_v,
                options.pro_e,
                options.res_k,
                options.radius_k,
                options.res_e,
                options.radius_e,
                options.smooth
                ]

    data = [wireframe]
    json.dump(data, f)

def make_obj(smooth, data):
   
    for i in range(0,len(LIST_EDGE_CONNECT)):
        if len(LIST_EDGE_CONNECT[i]) == bpy.types.Scene.res_e:
            vec_v = data[2]*data[0][i]
            LIST_VERT.append((vec_v.x,vec_v.y,vec_v.z))
            LIST_EDGE_CONNECT[i].append(len(LIST_VERT)-1)

    print("Vertices: ", len(LIST_VERT))
    print("Faces: ", len(LIST_FACE))
    dmh_mesh = bpy.data.meshes.new('dmh')
    dmh_mesh.from_pydata(LIST_VERT, [], LIST_FACE)

    bm = bmesh.new()
    bm.from_mesh(dmh_mesh)
    bm.verts.ensure_lookup_table()

    for i in range(0,len(LIST_EDGE_CONNECT)):
        if len(LIST_EDGE_CONNECT[i]) > 3:
            if (data[3][i] == 0.0):
                bmesh.ops.convex_hull(bm,input=[bm.verts[d] for d in LIST_EDGE_CONNECT[i]])    
    bm.to_mesh(dmh_mesh)
    
    bm.free
    dmh_obj = bpy.data.objects.new("DMH", dmh_mesh)
    bpy.context.scene.objects.link(dmh_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = bpy.data.objects[dmh_obj.name]
    bpy.data.objects[dmh_obj.name].select = True
    if (smooth):
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()

def do_it(context):
    # Debug Info
    zeit = time.time()
    print("Modelling Hull")     

    del LIST_VERT[:]
    del LIST_FACE[:]
    del LIST_EDGE_CONNECT[:]

    # Creating knots and edges
    type_k = bpy.types.Scene.type_k
    res_k = bpy.types.Scene.res_k
    res_e = bpy.types.Scene.res_e
    radius_k = bpy.types.Scene.radius_k
    radius_e = bpy.types.Scene.radius_e
    pro_e = bpy.types.Scene.pro_e
    pro_v = bpy.types.Scene.pro_v
    smooth = bpy.types.Scene.smooth
    data = bpy.types.Scene.data
    
    createKnots(data, type_k, pro_v, radius_k, res_k)
    createEdges(data, pro_e, radius_k, radius_e, res_e)


    make_obj(smooth, data)

    # Debug Info
    print("Finished in ", time.time() - zeit, " seconds.\n")
        
    return {'FINISHED'}

# Function to transform a source bMesh and copy the result to a target bMesh
# copyBmesh( 
#            source bMesh,
#            target bMesh,
#            scaling matrix,
#            rotation matrix,
#            translation matrix
#           )
def copyBmesh(src, sca, rot, loc):
    source = src.copy()
    start_index = len(LIST_VERT)
    
    # transform
    source.transform(matrix=sca)
    m = loc * rot
    source.transform(matrix=m)

    for v in source.verts:
        LIST_VERT.append((v.co.x,v.co.y,v.co.z))
    for f in source.faces:
        if len(f.verts) == 3:
            LIST_FACE.append([f.verts[0].index+start_index,f.verts[1].index+start_index,f.verts[2].index+start_index])
        elif len(f.verts) == 4:
            LIST_FACE.append([f.verts[0].index+start_index,f.verts[1].index+start_index,f.verts[2].index+start_index,f.verts[3].index+start_index])


# Function to create the hull for knots of a input object/tree
# createKnots( 
#               input object/tree,
#               target bMesh
#               )
def createKnots(data, type_k, pro_v, radius, res_k):
    # get world matrix and list of vertices of input object  
    om = data[2]
    listVertices = data[0]

    # Debug Info
    print("Starting to create ",len(listVertices) , " bMesh Knots")
    print("Knot-Type: ", type_k)
    
    # Create one model bMesh for knots        
    src = bmesh.new()
    if (type_k=="UV"):
        bmesh.ops.create_uvsphere(src, u_segments = res_k, v_segments = res_k, diameter = radius)
    elif (type_k=="ICO"):
        bmesh.ops.create_icosphere(src, subdivisions = res_k, diameter = radius)
    elif (type_k=="CUBE"):
        bmesh.ops.create_cube(src, size = radius*2)

    # Debug Info
    counter = 0    

    # For every knot    
    for i in range(0, len(listVertices)):
        counter += 1
        if (pro_v):
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

# Function to create the hull for edges of a input object/tree
# createEdges( 
#               input object/tree,
#               target bMesh
#               )    
def createEdges(data, pro_e, radius_k, radius_e, res_e):
    # transform input object/tree into bmesh
    om = data[2]
       
    # Create one model bMesh for edges
    src = bmesh.new()
    bmesh.ops.create_cone(src, segments=res_e, diameter1=radius_e, diameter2=radius_e, depth=1.0)

    # For every knot 
    for edge in data[1]:
        
        # Get coordinates of vertices of the edge
        vecA = om * data[0][edge[0]]
        vecB = om * data[0][edge[1]]

        # If the two vertices are not equal
        if ((vecA - vecB).length > 0):

            # calculate the distance between the two vertices            
            if radius_k-radius_e < 2*radius_e:
                dist = ((vecB) - (vecA)).length - (radius_k-radius_e)
            else:
                dist = ((vecB) - (vecA)).length - (2*radius_e)

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

            while ((len(LIST_EDGE_CONNECT)-1 < edge[0]) or (len(LIST_EDGE_CONNECT)-1 < edge[1])):
                LIST_EDGE_CONNECT.append([])          

            for i in range(len(LIST_VERT)-(2*res_e),len(LIST_VERT)):
                if (Vector(LIST_VERT[i])-vecA).length < (Vector(LIST_VERT[i])-vecB).length:
                    LIST_EDGE_CONNECT[edge[0]].append(i)
                else:
                    LIST_EDGE_CONNECT[edge[1]].append(i)

    # free memory		    
    src.free()

class dmh_add(bpy.types.Operator):
    '''Add a Wireframe Cover'''
    bl_idname = "mesh.dmh_add"
    bl_label = "Add a Wireframe Cover"
    bl_options = {'REGISTER', 'UNDO'}
 
    knot_types = [
    ("ICO", "Ico-Sphere", "", 1),
    ("UV", "UV-Sphere", "", 2),
    ("CUBE", "Cube", "", 3),
    ]

    def update_type_k(self, context):
        if self.type_k == "ICO":
            self.res_k = 2
        elif self.type_k == "CUBE":
            self.res_k = 0
        elif self.type_k == "UV":
            self.res_k = 8

    def update_res_k(self, context):
        min = 0
        print(self)
        if self.type_k == "ICO":
            min = 1
        elif self.type_k == "CUBE":
            self.res_k = 0
        elif self.type_k == "UV":
            min = 3
        if self.res_k < min:
            self.res_k = min

    def update_radius_k(self,context):
        if self.radius_k < self.radius_e:
            self.radius_k=self.radius_e

    def update_radius_e(self,context):
        if self.radius_e > self.radius_k:
            self.radius_e=self.radius_k

    type_k = EnumProperty(items=knot_types, default=DEFAULT_TYPE_K, name="Knot-Type", update=update_type_k)
    pro_v = BoolProperty(name="Knot PVR", default=DEFAULT_PRO_V)
    pro_e = BoolProperty(name="Edge PVR", default=DEFAULT_PRO_E)
    radius_k = FloatProperty(name="Knot-Radius", default=DEFAULT_RADIUS_K, min=0.001, max=100.0,update=update_radius_k)
    res_k = IntProperty(name="Knot-Resolution", default=DEFAULT_RES_K, min=0, max=128, update=update_res_k)
    radius_e = FloatProperty(name="Edge-Radius", default=DEFAULT_RADIUS_E, min=0.001, max=100.0,update=update_radius_e)
    res_e = IntProperty(name="Edge-Resolution", default=DEFAULT_RES_E, min=3, max=128)
    smooth = BoolProperty(name="Smooth-Shading", default=DEFAULT_SMOOTH)
    
    def execute(self, context):
        ACTUAL_STATE = DEFAULT_ACTUAL_STATE
        
        if (ACTUAL_STATE == "NEW"):
            self.type_k = DEFAULT_TYPE_K
            self.pro_v = DEFAULT_PRO_V
            self.pro_e = DEFAULT_PRO_E
            self.radius_k = DEFAULT_RADIUS_K
            self.res_k = DEFAULT_RES_K
            self.radius_e = DEFAULT_RADIUS_E
            self.res_e = DEFAULT_RES_E
            self.smooth = DEFAULT_SMOOTH

        if (ACTUAL_STATE == "IMPORT"):        
           
            self.type_k = IMPORT_TYPE_K
            self.pro_v = IMPORT_PRO_V
            self.pro_e = IMPORT_PRO_E
            self.radius_k = IMPORT_RADIUS_K
            self.res_k = IMPORT_RES_K
            self.radius_e = IMPORT_RADIUS_E
            self.res_e = IMPORT_RES_E
            self.smooth = IMPORT_SMOOTH
            
            dmh_tree_mesh = bpy.data.meshes.new('dmh_tree')
            dmh_tree_mesh.from_pydata(IMPORT_DATA[0], IMPORT_DATA[1], [])
            dmh_tree_obj = bpy.data.objects.new("DMH-TREE", dmh_tree_mesh)
            bpy.context.scene.objects.link(dmh_tree_obj)
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = bpy.data.objects[dmh_tree_obj.name]
            bpy.data.objects[dmh_tree_obj.name].select = True
            bpy.ops.transform.translate(value=IMPORT_DATA[2])
            for i in range(0, len(IMPORT_DATA[3])):
                bpy.context.selected_objects[0].data.vertices[i].bevel_weight = IMPORT_DATA[3][i]
                
        if (len(bpy.context.selected_objects)==1):
            obj = bpy.context.selected_objects[0]
            om = obj.matrix_world
            v = [vec.co for vec in obj.data.vertices]
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            e = []
            for edge in bm.edges:
                e.append([edge.verts[0].index, edge.verts[1].index])
            bw = [vec.bevel_weight for vec in obj.data.vertices]
            data = [v,e,om,bw]

            bpy.types.Scene.type_k = self.type_k
            bpy.types.Scene.pro_v = self.pro_v
            bpy.types.Scene.pro_e = self.pro_e
            bpy.types.Scene.res_k = self.res_k
            bpy.types.Scene.radius_k = self.radius_k
            bpy.types.Scene.res_e = self.res_e
            bpy.types.Scene.radius_e = self.radius_e
            bpy.types.Scene.smooth = self.smooth
            bpy.types.Scene.data = data
            
            new_obj = do_it(context)
        else:
            self.report({'INFO'}, 'No active object or to many selected objects.')
        return {'FINISHED'}
 
def menu_func(self, context):
    self.layout.operator("mesh.dmh_add", 
        text="Wireframe Cover", 
        icon='OUTLINER_OB_EMPTY')

class DMHImport(bpy.types.Operator, ImportHelper):
    """Import .dmh file Operator"""
    bl_idname = "i.dmh"
    bl_label = "Import DMH"

    def execute(self, context):
        path = "Importing " + self.properties.filepath
        self.report({'INFO'}, path)
        load_data(self.properties.filepath)
        return{'FINISHED'}

class DMHExport(bpy.types.Operator, ExportHelper):
    """Export .dmh file Operator"""
    bl_idname = "e.dmh"
    bl_label = "Export DMH"

    filename_ext = ".dmh"
    filter_glob = StringProperty(default="*.dmh", options={'HIDDEN'})

    def execute(self, context):
        path = "Exporting " + self.properties.filepath
        self.report({'INFO'}, path)
        save_data(self.properties.filepath)
        return{'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(
        DMHImport.bl_idname, text="DMH (.dmh)")

def menu_func_export(self, context):
    self.layout.operator(
        DMHExport.bl_idname, text="DMH (.dmh)")

def register():
   bpy.utils.register_module(__name__)
   bpy.types.INFO_MT_add.prepend(menu_func)
   bpy.types.INFO_MT_file_import.append(menu_func_import)
   bpy.types.INFO_MT_file_export.append(menu_func_export)
 
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.utils.register_module(ToolsPanel)
    bpy.types.INFO_MT_add.remove(menu_func)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()

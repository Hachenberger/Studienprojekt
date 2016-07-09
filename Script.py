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

    LIST_VERT = []
    LIST_FACE = []
    LIST_EDGE_CONNECT = [[]]
    
    #data = []

    DEFAULT_TYPE_K = "UV"
    DEFAULT_PRO_V = False
    DEFAULT_PRO_E = False
    DEFAULT_HIDE_K = False
    DEFAULT_RADIUS_K = 0.1
    DEFAULT_RES_K = 8
    DEFAULT_RADIUS_E = 0.03
    DEFAULT_RES_E = 6
    DEFAULT_SMOOTH = False
    DEFAULT_IMPORT = False
    DEFAULT_ACTUAL_STATE = "NEW"
    IMPORT_DATA = []
    IMPORT_TYPE_K = "UV"
    IMPORT_PRO_V = False
    IMPORT_PRO_E = False
    IMPORT_HIDE_K = False
    IMPORT_RADIUS_K = 0.1
    IMPORT_RES_K = 8
    IMPORT_RADIUS_E = 0.03
    IMPORT_RES_E = 6
    IMPORT_SMOOTH = False

    def __init__(self):
        print("Inititalising dmh_options...")
        
    def set_import(self,
                   import_data,
                   import_type_k,
                   import_pro_v,
                   import_pro_e,
                   import_hide_k,
                   import_res_k,
                   import_radius_k,
                   import_res_e,
                   import_radius_e,
                   import_smooth
                   ):
        self.IMPORT_DATA = import_data
        self.IMPORT_TYPE_K = import_type_k
        self.IMPORT_PRO_V = import_pro_v
        self.IMPORT_PRO_E = import_pro_e
        self.IMPORT_HIDE_K = import_hide_k
        self.IMPORT_RES_K = import_res_k
        self.IMPORT_RADIUS_K = import_radius_k
        self.IMPORT_RES_E = import_res_e
        self.IMPORT_RADIUS_E = import_radius_e
        self.IMPORT_SMOOTH = import_smooth
        
def load_data(fileName):
    f = open(fileName,'r')
    data_load = json.load(f)
    data = data_load[0]
    
    bpy.types.Scene.dmh.set_import([data[0],data[1],data[2],data[3]],
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
    
    bpy.types.Scene.dmh.DEFAULT_ACTUAL_STATE = "IMPORT"
    bpy.ops.mesh.dmh_add()
    bpy.types.Scene.dmh.DEFAULT_ACTUAL_STATE = "NEW"

def save_data(fileName):
    f = open(fileName,'w')
    
    list_vertices = []
    for v in bpy.types.Scene.dmh.data[0]:
        list_vertices.append([v[0],v[1],v[2]]) 
        
    options = bpy.types.Scene.dmh    
    
    world_pos = [options.data[2][0][3], options.data[2][1][3], options.data[2][2][3]]
      
    wireframe = [
                list_vertices, 
                options.data[1], world_pos, options.data[3],
                options.type_k,
                options.pro_v,
                options.pro_e,
                options.hide_k,
                options.res_k,
                options.radius_k,
                options.res_e,
                options.radius_e,
                options.smooth
                ]

    data = [wireframe]
    json.dump(data, f)

def make_obj(data):
    options = bpy.types.Scene.dmh  
   
    for i in range(0,len(options.LIST_EDGE_CONNECT)):
        if len(options.LIST_EDGE_CONNECT[i]) == options.res_e:
            vec_v = data[2]*data[0][i]
            options.LIST_VERT.append((vec_v.x,vec_v.y,vec_v.z))
            options.LIST_EDGE_CONNECT[i].append(len(options.LIST_VERT)-1)

    if options.pro_e:
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

    print("Vertices: ", len(options.LIST_VERT))
    print("Faces: ", len(options.LIST_FACE))
    dmh_mesh = bpy.data.meshes.new('dmh')
    dmh_mesh.from_pydata(options.LIST_VERT, [], options.LIST_FACE)

    bm = bmesh.new()
    bm.from_mesh(dmh_mesh)
    bm.verts.ensure_lookup_table()

    for i in range(0,len(options.LIST_EDGE_CONNECT)):
        if len(options.LIST_EDGE_CONNECT[i]) > 3:
            if (data[3][i] == 0.0):
                bmesh.ops.convex_hull(bm,input=[bm.verts[d] for d in options.LIST_EDGE_CONNECT[i]])    
    bm.to_mesh(dmh_mesh)
    
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

def do_it(context):
    # Debug Info
    zeit = time.time()
    print("Modelling Hull")     

    options = bpy.types.Scene.dmh  

    del options.LIST_VERT[:]
    del options.LIST_FACE[:]
    del options.LIST_EDGE_CONNECT[:]

    # Creating knots and edges
    
    createEdges(options.data, options.pro_e, options.radius_k, options.radius_e, options.res_e)
    createKnots(options.data, options.type_k, options.pro_v, options.hide_k, options.radius_k, options.res_k)


    make_obj(options.data)

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
    options = bpy.types.Scene.dmh
    
    source = src.copy()
    start_index = len(options.LIST_VERT)
    
    # transform
    source.transform(matrix=sca)
    m = loc * rot
    source.transform(matrix=m)

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
def createKnots(data, type_k, pro_v, hide_k, radius, res_k):
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
        if (not (hide_k and (len(bpy.types.Scene.dmh.LIST_EDGE_CONNECT[i]) == bpy.types.Scene.dmh.res_e * 2))):
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
    options = bpy.types.Scene.dmh 
    
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

            while ((len(options.LIST_EDGE_CONNECT)-1 < edge[0]) or (len(options.LIST_EDGE_CONNECT)-1 < edge[1])):
                options.LIST_EDGE_CONNECT.append([])          

            for i in range(len(options.LIST_VERT)-(2*res_e),len(options.LIST_VERT)):
                if (Vector(options.LIST_VERT[i])-vecA).length < (Vector(options.LIST_VERT[i])-vecB).length:
                    options.LIST_EDGE_CONNECT[edge[0]].append(i)
                else:
                    options.LIST_EDGE_CONNECT[edge[1]].append(i)

    # free memory		    
    src.free()



class dmh_add(bpy.types.Operator):
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
        if self.radius_k < self.radius_e*1.25:
            self.radius_k=self.radius_e*1.25

    def update_radius_e(self,context):
        if self.radius_e > self.radius_k*0.8:
            self.radius_e=self.radius_k*0.8

    options = bpy.types.Scene.dmh 

    type_k = EnumProperty(items=knot_types, default=options.DEFAULT_TYPE_K, name="Knot-Type", update=update_type_k)
    pro_v = BoolProperty(name="Knot PVR", default=options.DEFAULT_PRO_V)
    pro_e = BoolProperty(name="Edge PVR", default=options.DEFAULT_PRO_E)
    hide_k = BoolProperty(name="Hide knots with 2 edges", default=options.DEFAULT_HIDE_K)
    radius_k = FloatProperty(name="Knot-Radius", default=options.DEFAULT_RADIUS_K, min=0.001, max=100.0,update=update_radius_k)
    res_k = IntProperty(name="Knot-Resolution", default=options.DEFAULT_RES_K, min=0, max=128, update=update_res_k)
    radius_e = FloatProperty(name="Edge-Radius", default=options.DEFAULT_RADIUS_E, min=0.001, max=100.0,update=update_radius_e)
    res_e = IntProperty(name="Edge-Resolution", default=options.DEFAULT_RES_E, min=3, max=128)
    smooth = BoolProperty(name="Smooth-Shading", default=options.DEFAULT_SMOOTH)
      
    def execute(self, context):
        
        options = bpy.types.Scene.dmh 
        
        ACTUAL_STATE = options.DEFAULT_ACTUAL_STATE      
        
        if (ACTUAL_STATE == "NEW"):
            self.type_k = options.DEFAULT_TYPE_K
            self.pro_v = options.DEFAULT_PRO_V
            self.pro_e = options.DEFAULT_PRO_E
            self.hide_k = options.DEFAULT_HIDE_K
            self.radius_k = options.DEFAULT_RADIUS_K
            self.res_k = options.DEFAULT_RES_K
            self.radius_e = options.DEFAULT_RADIUS_E
            self.res_e = options.DEFAULT_RES_E
            self.smooth = options.DEFAULT_SMOOTH

        if (ACTUAL_STATE == "IMPORT"):        
           
            self.type_k = options.IMPORT_TYPE_K
            self.pro_v = options.IMPORT_PRO_V
            self.pro_e = options.IMPORT_PRO_E
            self.hide_k = options.IMPORT_HIDE_K
            self.radius_k = options.IMPORT_RADIUS_K
            self.res_k = options.IMPORT_RES_K
            self.radius_e = options.IMPORT_RADIUS_E
            self.res_e = options.IMPORT_RES_E
            self.smooth = options.IMPORT_SMOOTH
            
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
            om = obj.matrix_world
            v = [vec.co for vec in obj.data.vertices]
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            e = []
            for edge in bm.edges:
                e.append([edge.verts[0].index, edge.verts[1].index])
            bw = [vec.bevel_weight for vec in obj.data.vertices]
            data = [v,e,om,bw]

            options.type_k = self.type_k
            options.pro_v = self.pro_v
            options.pro_e = self.pro_e
            options.hide_k = self.hide_k
            options.res_k = self.res_k
            options.radius_k = self.radius_k
            options.res_e = self.res_e
            options.radius_e = self.radius_e
            options.smooth = self.smooth
            options.data = data
            
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

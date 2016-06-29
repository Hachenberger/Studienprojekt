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

list_vert = []
list_face = []
list_edge_connect = [[]]

def load_data(fileName):
    """Function to load a .dmh File

    :param fileName: Path and name of file 
    :type fileName: str. 
    :returns: none -- saving data in global lists list_vert and list_face 

    """ 
    f = open(fileName,'r')
    data = json.load(f)
    lv = data[0]
    for i in range(0,len(lv)):
        list_vert.append(lv[i])
    lf = data[1]
    for i in range(0,len(lf)):
        list_face.append(lf[i])
    make_obj(False)

def save_data(fileName):
    f = open(fileName,'w')
    data = [list_vert, list_face]
    json.dump(data, f)

def make_obj(smooth, data):
    
    for i in range(0,len(list_edge_connect)):
        if len(list_edge_connect[i]) == data[3]:
            vec_v = data[2]*data[0][i].co
            list_vert.append((vec_v.x,vec_v.y,vec_v.z))
            list_edge_connect[i].append(len(list_vert)-1)

    print("Vertices: ", len(list_vert))
    print("Faces: ", len(list_face))
    dmh_mesh = bpy.data.meshes.new('dmh')
    dmh_mesh.from_pydata(list_vert, [], list_face)

    bm = bmesh.new()
    bm.from_mesh(dmh_mesh)
    bm.verts.ensure_lookup_table()

    for i in range(0,len(list_edge_connect)):
        if len(list_edge_connect[i]) > 3:
            if (data[0][i].bevel_weight == 0.0):
                bmesh.ops.convex_hull(bm,input=[bm.verts[d] for d in list_edge_connect[i]])    
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

def do_it(context, type_k, pro_v, pro_e, radius_k, res_k, radius_e, res_e, smooth, data):
    # Debug Info
    zeit = time.time()
    print("Modelling Hull")     

    del list_vert[:]
    del list_face[:]
    del list_edge_connect[:]

    # Creating knots and edges
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
    start_index = len(list_vert)
    
    # transform
    source.transform(matrix=sca)
    m = loc * rot
    source.transform(matrix=m)

    for v in source.verts:
        list_vert.append((v.co.x,v.co.y,v.co.z))
    for f in source.faces:
        if len(f.verts) == 3:
            list_face.append([f.verts[0].index+start_index,f.verts[1].index+start_index,f.verts[2].index+start_index])
        elif len(f.verts) == 4:
            list_face.append([f.verts[0].index+start_index,f.verts[1].index+start_index,f.verts[2].index+start_index,f.verts[3].index+start_index])


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
            bw = listVertices[i].bevel_weight
        else:
            bw = 1.0
        if (bw != 0.0):
            lc = listVertices[i].co
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
        vecA = om * data[0][edge.verts[0].index].co
        vecB = om * data[0][edge.verts[1].index].co

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

            while ((len(list_edge_connect)-1 < edge.verts[0].index) or (len(list_edge_connect)-1 < edge.verts[1].index)):
                list_edge_connect.append([])          

            for i in range(len(list_vert)-(2*res_e),len(list_vert)):
                if (Vector(list_vert[i])-vecA).length < (Vector(list_vert[i])-vecB).length:
                    list_edge_connect[edge.verts[0].index].append(i)
                else:
                    list_edge_connect[edge.verts[1].index].append(i)

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
            self.res_k = 1
        elif self.type_k == "CUBE":
            self.res_k = 0
        elif self.type_k == "UV":
            self.res_k = 4

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

    type_k = EnumProperty(items=knot_types, default="UV", name="Knot-Type", update=update_type_k)
    pro_v = BoolProperty(name="Knot PVR", default=False)
    pro_e = BoolProperty(name="Edge PVR", default=False)
    radius_k = FloatProperty(name="Knot-Radius", default=0.1, min=0.001, max=100.0,update=update_radius_k)
    res_k = IntProperty(name="Knot-Resolution", default=8, min=0, max=128, update=update_res_k)
    radius_e = FloatProperty(name="Edge-Radius", default=0.03, min=0.001, max=100.0,update=update_radius_e)
    res_e = IntProperty(name="Edge-Resolution", default=6, min=3, max=128)
    smooth = BoolProperty(name="Smooth-Shading", default=False)

    def execute(self, context):
        if (len(bpy.context.selected_objects)==1):
            obj = bpy.context.selected_objects[0]
            om = obj.matrix_world
            v = obj.data.vertices
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            e = bm.edges
            data = [v,e,om,self.res_e]

            new_obj = do_it(context, self.type_k, self.pro_v, self.pro_e,
                self.radius_k, self.res_k, self.radius_e, self.res_e, self.smooth, data)
        else:
            self.report({'INFO'}, 'No active object.')
        return {'FINISHED'}
 
def menu_func(self, context):
    self.layout.operator("mesh.dmh_add", 
        text="Wireframe Cover", 
        icon='OUTLINER_OB_EMPTY')

class DMHImport(bpy.types.Operator, ImportHelper):
    """Import .dmh file Operator"""

    #: Name of function for calling the nif export operator.
    bl_idname = "i.dmh"

    #: How the nif import operator is labelled in the user interface.
    bl_label = "Import DMH"

    def execute(self, context):
        path = "Importing " + self.properties.filepath
        self.report({'INFO'}, path)
        load_data(self.properties.filepath)
        return{'FINISHED'}

class DMHExport(bpy.types.Operator, ExportHelper):
    """Export .dmh file Operator"""

    #: Name of function for calling the nif export operator.
    bl_idname = "e.dmh"

    #: How the nif import operator is labelled in the user interface.
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

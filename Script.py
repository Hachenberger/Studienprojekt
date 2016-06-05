import bpy
import bmesh
from math import *
from mathutils import *
from bpy.props import *
import bmesh
import math
import mathutils
import time


def do_it(context, radius_k, res_k, radius_e, res_e, src_obj):
    # Debug Info
    zeit = time.time()
    print("Modelling Hull")     

    # Creating Object und bMesh for the result of the script
    dmh_mesh = bpy.data.meshes.new('dmh')
    hull_obj = bpy.data.objects.new('Hull', dmh_mesh)
    bpy.context.scene.objects.link(hull_obj)        
    dmh_bmesh = bmesh.new()
		
    # Creating knots and edges
    createKnots(bpy.data.objects[src_obj], dmh_bmesh, radius_k, res_k)
    createEdges(bpy.data.objects[src_obj], dmh_bmesh, radius_e, res_e)
        
    # Copy results to the result object and free the memory
    dmh_bmesh.to_mesh(dmh_mesh)
    dmh_bmesh.free()		

    # Debug Info
    print("Finished in ", time.time() - zeit, " seconds.")
        
    return {'FINISHED'}

# Function to transform a source bMesh and copy the result to a target bMesh
# copyBmesh( 
#            source bMesh,
#            target bMesh,
#            scaling matrix,
#            rotation matrix,
#            translation matrix
#           )
def copyBmesh(src, dmh_bmesh, sca, rot, loc):
    source = src.copy()
    verts = [vert.co for vert in source.verts]
    faces = [face.verts for face in source.faces]
    
    # transform
    source.transform(matrix=sca)
    m = loc * rot
    source.transform(matrix=m)
    
    # copy
    for faceIndex in range(0, len(faces)):
        dmh_bmesh.faces.new([dmh_bmesh.verts.new(verts[faces[faceIndex][o].index]) for o in range(0, len(faces[faceIndex]))])

# Function to create the hull for knots of a input object/tree
# createKnots( 
#               input object/tree,
#               target bMesh
#               )
def createKnots(this_object, dmh_bmesh, radius, res_k):
    # get world matrix and list of vertices of input object  
    om = this_object.matrix_world  
    listVertices = this_object.data.vertices 

    # Debug Info
    print("Starting to create ",len(listVertices) , " bMesh Knots")
    
    # Create one model bMesh for knots        
    src = bmesh.new()
    bmesh.ops.create_uvsphere(src, u_segments = res_k, v_segments = res_k, diameter = radius)

    # Debug Info
    counter = 0    

    # For every knot    
    for i in range(0, len(listVertices)):
        counter += 1
        lc = listVertices[i].co  
        v = om * lc 
        # Scaling matrix 
        sca = Matrix.Scale(1.0, 4, (0.0, 0.0, 1.0)) * Matrix.Scale(1.0, 4, (0.0, 1.0, 0.0)) * Matrix.Scale(1.0, 4, (1.0, 0.0, 0.0))
        # Rotation matrix
        rot = Euler((0.0, 0.0, 0.0)).to_matrix().to_4x4()
        # Translation matrix
        loc = Matrix.Translation(v)
        # Copy model bMesh to target bMesh
        copyBmesh(src, dmh_bmesh, sca, rot, loc)
		    
    # Free memory
    src.free()
    
    # Debug Infos                
    print("Created ", counter, " Knots")
    print("Anzahl Vertices: ", len(dmh_bmesh.verts))
    print("Anzahle edges: ", len(dmh_bmesh.edges))
    print("Anzahle faces: ", len(dmh_bmesh.faces))       

# Function to calculate the distance between two 3d vertices
def calcEdgeLength(vecA, vecB):
    a = pow(vecA[0] - vecB[0], 2)
    b = pow(vecA[1] - vecB[1], 2)
    c = pow(vecA[2] - vecB[2], 2)
    result = sqrt(a + b + c)
    return result

# Function to create the hull for edges of a input object/tree
# createEdges( 
#               input object/tree,
#               target bMesh
#               )    
def createEdges(this_object, dmh_bmesh, radius, res_e):
    # transform input object/tree into bmesh
    bMesh = bmesh.new()
    bMesh.from_mesh(this_object.data)
    om = this_object.matrix_world 
       
    # Create one model bMesh for edges
    src = bmesh.new()
    bmesh.ops.create_cone(src, segments=res_e, diameter1=radius, diameter2=radius, depth=1.0)

    # For every knot 
    for edge in bMesh.edges:
        
        # Get coordinates of vertices of the edge
        vecA = edge.verts[0].co
        vecB = edge.verts[1].co

        # If the two vertices are not equal
        if ((vecA - vecB).length > 0):

            # calculate the distance between the two vertices            
            dist = ((vecB * om) - (vecA * om)).length

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
            loc = Matrix.Translation(om*location)
            # Copy model bMesh to target bMesh        
            copyBmesh(src, dmh_bmesh, sca, rot, loc)

    # free memory		    
    src.free()

class dmh_add(bpy.types.Operator):
    '''Add a Wireframe Cover'''
    bl_idname = "mesh.dmh_add"
    bl_label = "Add a Wireframe Cover"
    bl_options = {'REGISTER', 'UNDO'}
 
    radius_k = FloatProperty(name="Knot-Radius", default=0.1, min=0.001, max=100.0)
    res_k = IntProperty(name="Knot-Resolution", default=8, min=4, max=128)
    radius_e = FloatProperty(name="Edge-Radius", default=0.03, min=0.001, max=100.0)
    res_e = IntProperty(name="Edge-Resolution", default=6, min=3, max=128)

    def obj_list(self, context):  
        return [(o.name, o.name, o.type) for o in bpy.context.scene.objects]
 
    def execute(self, context):
        if (bpy.context.active_object):
            new_obj = do_it(context, 
                self.radius_k, self.res_k, self.radius_e, self.res_e, bpy.context.active_object.name)
        else:
            self.report({'INFO'}, 'No active object.')
        return {'FINISHED'}
 
def menu_func(self, context):
    self.layout.operator("mesh.dmh_add", 
        text="Wireframe Cover", 
        icon='OUTLINER_OB_EMPTY')
 
def register():
   bpy.utils.register_module(__name__)
   bpy.types.INFO_MT_add.prepend(menu_func)
 
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_add.remove(menu_func)
 
if __name__ == "__main__":
    register()
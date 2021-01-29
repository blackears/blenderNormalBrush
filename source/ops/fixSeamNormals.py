import bpy
import bpy.utils.previews
import bmesh
import mathutils
import math


#---------------------------

#class FixSeamNormalsSettings(bpy.types.PropertyGroup):
##    operation_type : bpy.props.EnumProperty(
##        items=(
##            ('ACTIVE_TO_SELECTED', "Active", "Copy normals from active mesh to all selected ones"),
##            ('COMBINED', "Combined", "Use faces of all selected meshes to calculate seam normal")
##        ),
##        default='ACTIVE_TO_SELECTED'
##    )

##    distance : bpy.props.FloatProperty(
##        name="Distance", description="Maximum gap between vertices.", default = .000001, min=0, soft_max = .001
##    )
#    pass

#---------------------------

class FixSeamNormalsOperator(bpy.types.Operator):
    """Copy normals from active mest to selected meshes along seam"""
    bl_idname = "kitfox.nt_fix_seam_normals"
    bl_label = "Fix Seam Normals"

    seam_verts = []

    def combined_normal(self, context, vertexCo):
        
        sum = mathutils.Vector((0, 0, 0))
        count = 0
        
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj != context.active_object:
                sel_mesh = obj.data
                
                for p in sel_mesh.polygons:
                    v0 = sel_mesh.vertices[p.vertices[0]]
                    v1 = sel_mesh.vertices[p.vertices[1]]
                    v2 = sel_mesh.vertices[p.vertices[2]]
                    
                    if v0.co == vertexCo or v1.co == vertexCo or v2.co == vertexCo:
                        sum = sum + p.normal
                        count = count + 1
                        
        sum.normalize()
        return sum
                        
#                    for i, ek in enumerate(sel_mesh.edge_keys):
#                        edge = sel_mesh.edges[i]
#                        print ("edge " + str(edge))

#                        v0 = sel_mesh.vertices[edge.vertices[0]]
#                        v1 = sel_mesh.vertices[edge.vertices[1]]
#                        
#                        if v0.co == vertex.co:
#                            off = mathutils.Vector(v1.co) - mathutils.Vector(v0.co)
#                            
                        
                        
##                        

#        pass
                    
#                    for loop_index in p.loop_indices:
#                        ls = sel_mesh.loops[loop_index]
#                        vs = sel_mesh.vertices[ls.vertex_index]
#                        #norm = ls.normal
                        
                        
                        
                
        
        
        
    def combined(self, context, active_mesh):
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj != context.active_object:
                sel_mesh = obj.data
                
                sel_mesh.use_auto_smooth = True
                normals = []
                sel_mesh.calc_normals_split()
                
                for p in sel_mesh.polygons:
                    for loop_index in p.loop_indices:
                        ls = sel_mesh.loops[loop_index]
                        vs = sel_mesh.vertices[ls.vertex_index]
                        norm = ls.normal
                        
                        for la in self.seam_verts:
                            va = active_mesh.vertices[la.vertex_index]
                            if va.co == vs.co:
                                norm = self.combined_normal(context, vs.co)
                        
                        normals.append(norm)
                    
                sel_mesh.normals_split_custom_set(normals)
        

    def active_to_selected(self, context, active_mesh):
        active_mesh.calc_normals_split()

        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj != context.active_object:
                sel_mesh = obj.data
    
#                print("OBJECT " + obj.name)
                
                sel_mesh.use_auto_smooth = True
                normals = []
                sel_mesh.calc_normals_split()
                
                for p in sel_mesh.polygons:
                    for loop_index in p.loop_indices:
                        ls = sel_mesh.loops[loop_index]
                        
                        vs = sel_mesh.vertices[ls.vertex_index]
                        norm = ls.normal
#                        print("norm  ls.index " + str(ls.index) + " vs idx:" + str(vs.index) + "  co " + str(vs.co) + "  norm " + str(ls.normal))
                        
                        for la in active_mesh.loops:
                            va = active_mesh.vertices[la.vertex_index]
#                            print("passing vertex " + str(va.index) + " co " + str(va.co))
                            if (va.co == vs.co):
#                                print("Match norm  va idx:" + str(va.index) + "  co " + str(va.co) + "  norm " + str(la.normal))
                                norm = la.normal
#                            break
                        normals.append(norm)
                    
                sel_mesh.normals_split_custom_set(normals)
            
        

    def find_partner(self, context, active_mesh, la):
        
        va = active_mesh.vertices[la.vertex_index]
        
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj != context.active_object:
                sel_mesh = obj.data
                
                for ls in sel_mesh.loops:
                    vs = sel_mesh.vertices[ls.vertex_index]
                    if va.co == vs.co:
                        self.seam_verts.append(la)
#                        print ("adding vert  va.index" + str(va.index) + " vs.index" + str(vs.index) + " co " + str(va.co))
#                        print ("la.index " + str(la.index) + "  ls.index " + str(ls.index))
                        return

            
    def execute(self, context):
        self.seam_verts = []
        
        active = context.active_object
        if active == None or active.type != 'MESH':
            print ("No active object selected or active object is not a mesh")
            return {'FINISHED'}

        active_mesh = active.data
        
        for la in active_mesh.loops:
            self.find_partner(context, active_mesh, la)

#        operation_type = context.scene.fix_seam_normals_tool.operation_type

        self.active_to_selected(context, active_mesh)
                    
#        if operation_type == "ACTIVE_TO_SELECTED":
#            self.active_to_selected(context, active_mesh)
#        else:
#            self.combined(context, active_mesh)
#    
        return {'FINISHED'}
        
#---------------------------

class FixSeamNormalPropsPanel(bpy.types.Panel):

    """Properties Panel for the Normal Tool on tool shelf"""
    bl_label = "Fix Seam Normals"
    bl_idname = "OBJECT_PT_fix_seam_normals_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kitfox"

        

    def draw(self, context):
        layout = self.layout

        scene = context.scene
#        settings = scene.fix_seam_normals_tool
        

#        row = layout.row();
#        row.prop(settings, "operation_type", expand = True)
        
        col = layout.column();
#        col.prop(settings, "distance")
        col.operator("kitfox.nt_fix_seam_normals", text="Copy Seam Normals")
        
#---------------------------

class SeparateWithNormalsOperator(bpy.types.Operator):
    """Separate selected faces from mesh but presserve normals"""
    bl_idname = "kitfox.nt_fix_seam_normals"
    bl_label = "Fix Seam Normals"

    def execute(self, context):
        
        active = context.active_object
        if active == None or active.type != 'MESH':
            print ("No active object selected or active object is not a mesh")
            return {'FINISHED'}

        active_mesh = active.data
        
        bm = bmesh.new()
        bm.from_mesh(active_mesh)
        

#---------------------------

def register():

#    bpy.utils.register_class(FixSeamNormalsSettings)
    bpy.utils.register_class(FixSeamNormalsOperator)
    bpy.utils.register_class(FixSeamNormalPropsPanel)

#    bpy.types.Scene.fix_seam_normals_tool = bpy.props.PointerProperty(type=FixSeamNormalsSettings)



def unregister():
#    bpy.utils.unregister_class(FixSeamNormalsSettings)
    bpy.utils.unregister_class(FixSeamNormalsOperator)
    bpy.utils.unregister_class(FixSeamNormalPropsPanel)

    del bpy.types.Scene.fix_seam_normals_tool
    


if __name__ == "__main__":
    register()

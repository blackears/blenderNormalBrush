# This file is part of the Kitfox Normal Brush distribution (https://github.com/blackears/blenderNormalBrush).
# Copyright (c) 2021 Mark McKay
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy
import bpy.utils.previews
import bmesh
import mathutils
import math



#---------------------------

class FixSeamNormalsOperator(bpy.types.Operator):
    """Copy normals from active mesh to selected meshes along seam"""
    bl_idname = "kitfox.nt_fix_seam_normals"
    bl_label = "Fix Seam Normals"
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self):
        self.seam_verts = []

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
                
                sel_mesh.use_auto_smooth = True
                normals = []
                sel_mesh.calc_normals_split()
                
                for p in sel_mesh.polygons:
                    for loop_index in p.loop_indices:
                        ls = sel_mesh.loops[loop_index]
                        
                        vs = sel_mesh.vertices[ls.vertex_index]
                        norm = ls.normal
                        
                        for la in active_mesh.loops:
                            va = active_mesh.vertices[la.vertex_index]
                            if (va.co == vs.co):
                                norm = la.normal
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

        self.active_to_selected(context, active_mesh)
                    
        return {'FINISHED'}
        
#---------------------------

class FixSeamNormalPropsPanel(bpy.types.Panel):

    """Properties Panel for the Normal Tool on tool shelf"""
    bl_label = "Fix Seam Normals"
    bl_idname = "OBJECT_PT_fix_seam_normals_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kitfox - Normal"

        

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        
        col = layout.column();
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

    bpy.utils.register_class(FixSeamNormalsOperator)
    bpy.utils.register_class(FixSeamNormalPropsPanel)



def unregister():
    bpy.utils.unregister_class(FixSeamNormalsOperator)
    bpy.utils.unregister_class(FixSeamNormalPropsPanel)

    


if __name__ == "__main__":
    register()

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


"""
            
    def execute_(self, context):
        self.seam_verts = []
        
        active = context.active_object
        if active == None or active.type != 'MESH':
            self.report({"WARNING"}, "No active object selected or active object is not a mesh")
#            push_error("No active object selected or active object is not a mesh")
            return {'FINISHED'}

        active_mesh = active.data
        
        for la in active_mesh.loops:
            self.find_partner(context, active_mesh, la)

        self.active_to_selected(context, active_mesh)
                    
        return {'FINISHED'}

###################
###################
###################
###################

    def execute_2(self, context):
        epsilon = .00001
        
        active = context.active_object
        neighbors = [p for p in context.selected_objects if p.type == 'MESH' and p != context.active_object]
        
        if active == None or active.type != 'MESH':
            self.report({"WARNING"}, "No active object selected or active object is not a mesh")
            return {'CANCELLED'}

        weighted_normal = mathutils.Vector((0, 0, 0))

        for la in active_mesh.loops:
            mesh_l = active_mesh.data
            
            for neighbor in neighbors:
                mesh_p = neighbor.data
                for lp in in mesh_p.loops:
                    vp = mesh.vertices[lp.vertex_index]
                    if (vl.co - vp.co).length < epsilon:
                        weighted_normal += vp.
                        
                    
            
            #for l_peer in 
            
            
            #self.find_partner(context, active_mesh, la)

"""

import bpy
import bpy.utils.previews
import bmesh
import mathutils
import math



#---------------------------

class CopySeamNormalsOperator(bpy.types.Operator):
    """Copy normals from active mesh to selected meshes along seam."""
    bl_idname = "kitfox.nt_copy_seam_normals"
    bl_label = "Copy Seam Normals"
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
        epsilon = .00001
        
        active_obj = context.active_object
        if not active_obj.type == 'MESH':
            self.report({"WARNING"}, "Active object is not a mesh")
            return {'CANCELLED'}
        
        neighbor_objs = [p for p in context.selected_objects if p.type == 'MESH' and p != context.active_object]
        if not neighbor_objs:
            self.report({"WARNING"}, "No objects to copy to selected")
            return {'CANCELLED'}

        bm = bmesh.new()
        bm.from_mesh(active_obj.data)
        
        update_loops = []
        
        for face in bm.faces:
            for lp in face.loops:
                if lp.edge.is_boundary or lp.link_loop_prev.edge.is_boundary:
                    update_loops.append(lp)

        for nobj in neighbor_objs:
            mesh = nobj.data
            
            normals = []

            for loop in mesh.loops:
                vert = mesh.vertices[loop.vertex_index]
                
                normal = mathutils.Vector((0, 0, 0))
                for lp in update_loops:
                    if (lp.vert.co - vert.co).length < epsilon:
                        normal = lp.calc_normal()
                        break
                
                normals.append(normal)
                
            mesh.normals_split_custom_set(normals)

        return {'FINISHED'}

#---------------------------

class SmoothSeamNormalsOperator(bpy.types.Operator):
    """Calculate smoothed normal on boundary vertices where they are coincident with vertices of adjacent meshes."""
    bl_idname = "kitfox.nt_smooth_seam_normals"
    bl_label = "Smooth Seam Normals"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        epsilon = .00001
        
        objs = [p for p in context.selected_objects if p.type == 'MESH']
        if not objs:
            self.report({"WARNING"}, "No active object selected or active object is not a mesh")
            return {'CANCELLED'}

        bm_meshes = []
        for obj in objs:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm_meshes.append(bm)

        #Find loops on edge
        update_loops = []
        update_normals = {}
        
        for obj, bm in zip(objs, bm_meshes):
            for face in bm.faces:
                for lp in face.loops:
                    if lp.edge.is_boundary or lp.link_loop_prev.edge.is_boundary:
                        update_loops.append((obj, bm, lp))


        for obj, bm, loop_focus in update_loops:
            weighted_normal = mathutils.Vector((0, 0, 0))
            
            for obj_peer, bm_peer, loop_peer in update_loops:
                if (loop_peer.vert.co - loop_focus.vert.co).length < epsilon:
                    weighted_normal += loop_peer.face.normal * loop_peer.calc_angle()
           
            weighted_normal.normalize()
            key = (obj.name, loop_focus.index)
            update_normals[key] = weighted_normal
            
        for obj in objs:
            mesh = obj.data
            
            normals = []
            for loop in mesh.loops:
                key = (obj.name, loop.index)
                if key in update_normals:
                    normals.append(update_normals[key])
                else:
                    normals.append(mathutils.Vector((0, 0, 0)))
                
            mesh.normals_split_custom_set(normals)
        
        #Write back to source meshes
        for bm, obj in zip(bm_meshes, objs):
            bm.free()
            
        return {'FINISHED'}
        
#---------------------------

class SeamNormalPropsPanel(bpy.types.Panel):

    """Properties Panel for the Normal Tool on tool shelf"""
    bl_label = "Seam Normals"
    bl_idname = "OBJECT_PT_seam_normals_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kitfox - Normal"


    def draw(self, context):
        layout = self.layout

        scene = context.scene
        
        col = layout.column();
        col.operator("kitfox.nt_copy_seam_normals")
        col.operator("kitfox.nt_smooth_seam_normals")


#---------------------------

def register():

    bpy.utils.register_class(SmoothSeamNormalsOperator)
    bpy.utils.register_class(CopySeamNormalsOperator)
    bpy.utils.register_class(SeamNormalPropsPanel)



def unregister():
    bpy.utils.unregister_class(SmoothSeamNormalsOperator)
    bpy.utils.unregister_class(CopySeamNormalsOperator)
    bpy.utils.unregister_class(SeamNormalPropsPanel)
    # bpy.utils.unregister_class(FixSeamNormalsOperator)
    # bpy.utils.unregister_class(FixSeamNormalPropsPanel)

    


if __name__ == "__main__":
    register()

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
import os
import bgl
import blf
import gpu
import mathutils
import math
import bmesh

from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

def ray_cast(context, viewlayer, ray_origin, view_vector):
    if bpy.app.version >= (2, 91, 0):
        return context.scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)
    else:
        return context.scene.ray_cast(viewlayer, ray_origin, view_vector)


def redraw_all_viewports(context):
    for area in bpy.context.screen.areas: # iterate through areas in current screen
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class NormalToolSettings(bpy.types.PropertyGroup):
    brush_type : bpy.props.EnumProperty(
        items=(
            ('COMB', "Comb", "Normals point in the direction that the brush moves"),
            ('FIXED', "Fixed", "Normals are in a fixed direction"),
            ('ATTRACT', "Attract", "Normals point toward target object"),
            ('REPEL', "Repel", "Normals point away from target object"),
            ('SMOOTH', "Smooth", "Average the normal direction under the brush"),
            ('VERTEX', "Vertex", "Get normal values from mesh vertices")
        ),
        default='COMB'
    )
    
    radius : bpy.props.FloatProperty(
        name="Radius", 
        description="Radius of brush", 
        default = 1, 
        min = 0, 
        soft_max = 4
    )
    
    strength : bpy.props.FloatProperty(
        name="Strength", 
        description="Amount to adjust mesh normal", 
        default = 1, 
        min = 0, 
        max = 1
    )

    use_pressure : bpy.props.BoolProperty(
        name="Pen Pressure", 
        description="If true, pen pressure is used to adjust strength", 
        default = True
    )
    
    normal_length : bpy.props.FloatProperty(
        name = "Normal Length", 
        description="Display length of normal", 
        default = 1, 
        min=0, 
        soft_max = 1
    )

    selected_verts_only : bpy.props.BoolProperty(
        name = "Selected Vertices Only", 
        description = "If true, affect only selected vertices", 
        default = False
    )

    selected_faces_only : bpy.props.BoolProperty(
        name = "Selected Faces Only", 
        description = "If true, affect only selected faces", 
        default = False
    )

    normal : bpy.props.FloatVectorProperty(
        name = "Normal", 
        description = "Direction of normal in Fixed mode", 
        default = (1, 0, 0), 
        subtype = "DIRECTION"
    )
    
    normal_exact : bpy.props.BoolProperty(
        name = "Exact normal", 
        description = "Display normal as exact coordinates",
        default = True
    )
    
    front_faces_only : bpy.props.BoolProperty(
        name = "Front Faces Only", 
        description = "Only affect normals on front facing faces", 
        default = True
    )

    target : bpy.props.PointerProperty(
        name = "Target", 
        description = "Object Attract and Repel mode reference", 
        type = bpy.types.Object
    )
    
    symmetry_x : bpy.props.BoolProperty(
        name="X", 
        description = "Symmetry across the X axis",
        default = False
    )
    
    symmetry_y : bpy.props.BoolProperty(
        name = "Y", 
        description = "Symmetry across the Y axis", 
        default = False
    )
    
    symmetry_z : bpy.props.BoolProperty(
        name = "Z", 
        description = "Symmetry across the Z axis", 
        default = False
    )
    

#---------------------------
        

circleSegs = 64
coordsCircle = [(math.sin(((2 * math.pi * i) / circleSegs)), math.cos((math.pi * 2 * i) / circleSegs), 0) for i in range(circleSegs + 1)]

coordsNormal = [(0, 0, 0), (0, 0, 1)]

vecZ = mathutils.Vector((0, 0, 1))
vecX = mathutils.Vector((1, 0, 0))

shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
batchLine = batch_for_shader(shader, 'LINES', {"pos": coordsNormal})
batchCircle = batch_for_shader(shader, 'LINE_STRIP', {"pos": coordsCircle})


#Find matrix that will rotate Z axis to point along normal
#coord - point in world space
#normal - normal in world space
def calc_vertex_transform_world(pos, norm):
    axis = norm.cross(vecZ)
    if axis.length_squared < .0001:
        axis = mathutils.Vector(vecX)
    else:
        axis.normalize()
    angle = -math.acos(norm.dot(vecZ))
    
    quat = mathutils.Quaternion(axis, angle)
    mR = quat.to_matrix()
    mR.resize_4x4()
    
    mT = mathutils.Matrix.Translation(pos)

    m = mT @ mR
    return m

#Calc matrix that maps from world space to a particular vertex on mesh
#coord - vertex position in local space
#normal - vertex normal in local space
def calc_vertex_transform(obj, coord, normal):
    pos = obj.matrix_world @ coord

    #Transform normal into world space
    norm = mathutils.Vector((normal.x, normal.y, normal.z, 0))
    mIT = obj.matrix_world.copy()
    mIT.invert()
    mIT.transpose()
    norm = mIT @ norm
    norm.resize_3d()
    norm.normalize()

    return calc_vertex_transform_world(pos, norm)


def calc_gizmo_transform(obj, coord, normal, ray_origin):
    mV = calc_vertex_transform(obj, coord, normal)
    
    pos = obj.matrix_world @ coord
    
    eye_offset = pos - ray_origin
    radius = eye_offset.length / 5
    mS = mathutils.Matrix.Scale(radius, 4)

    m = mV @ mS
    return m


def draw_callback(self, context):
    ctx = bpy.context

    region = context.region
    rv3d = context.region_data

    viewport_center = (region.x + region.width / 2, region.y + region.height / 2)
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, viewport_center)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, viewport_center)


    shader.bind();

    bgl.glEnable(bgl.GL_DEPTH_TEST)
    
    #Draw cursor
    if self.show_cursor:
        brush_radius = context.scene.normal_brush_props.radius
    
        m = calc_vertex_transform_world(self.cursor_pos, self.cursor_normal);
        mS = mathutils.Matrix.Scale(brush_radius, 4)
        m = m @ mS
    
        #Tangent to mesh
        gpu.matrix.push()
        
        gpu.matrix.multiply_matrix(m)

        shader.uniform_float("color", (1, 0, 1, 1))
        batchCircle.draw(shader)
        
        gpu.matrix.pop()


        #Brush normal direction
        brush_type = context.scene.normal_brush_props.brush_type
        brush_normal = context.scene.normal_brush_props.normal
        
        if brush_type == "FIXED":
            gpu.matrix.push()
            
            m = calc_vertex_transform_world(self.cursor_pos, brush_normal);
            gpu.matrix.multiply_matrix(m)

            shader.uniform_float("color", (0, 1, 1, 1))
            batchLine.draw(shader)
            
            gpu.matrix.pop()

    
    #Draw editable normals
    shader.uniform_float("color", (1, 1, 0, 1))


    normLength = context.scene.normal_brush_props.normal_length
    mS = mathutils.Matrix.Scale(normLength, 4)

    shader.uniform_float("color", (1, 1, 0, 1))

    for obj in ctx.selected_objects:
        if obj.type == 'MESH':
            success = obj.update_from_editmode()
            mesh = obj.data

            mesh.calc_normals_split()
            coordsNormals = []
            
            for l in mesh.loops:
                    
                v = mesh.vertices[l.vertex_index]
                coordsNormals.append(v.co)
                coordsNormals.append(v.co + l.normal * normLength)

            batchNormals = batch_for_shader(shader, 'LINES', {"pos": coordsNormals})
    
            gpu.matrix.push()
            
            gpu.matrix.multiply_matrix(obj.matrix_world)
            batchNormals.draw(shader)
            
            gpu.matrix.pop()

    bgl.glDisable(bgl.GL_DEPTH_TEST)



#---------------------------

class ModalDrawOperator(bpy.types.Operator):
    """Adjust normals"""
    bl_idname = "kitfox.normal_tool"
    bl_label = "Normal Tool Kitfox"
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self):
        self.dragging = False
        
        self.cursor_pos = None
        self.show_cursor = False
        
        self.history = []
        self.history_idx = -1
        self.history_limit = 10
        self.history_bookmarks = {}
        
        self.stroke_trail = []
        
    def free_snapshot(self, map):
        for obj in map:
            bm = map[obj]
            bm.free()

    #if bookmark is other than -1, snapshot added to bookmark library rather than undo stack
    def history_snapshot(self, context, bookmark = -1):
        map = {}
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = bmesh.new()
                
                mesh = obj.data
                bm.from_mesh(mesh)
                map[obj] = bm
                
        if bookmark != -1:
            self.history_bookmarks[bookmark] = map
                
        else:
            #Remove first element if history queue is maxed out
            if self.history_idx == self.history_limit:
                self.free_snapshot(self.history[0])
                self.history.pop(0)
            
                self.history_idx += 1

            #Remove all history past current pointer
            while self.history_idx < len(self.history) - 1:
                self.free_snapshot(self.history[-1])
                self.history.pop()
                    
            self.history.append(map)
            self.history_idx += 1
        
    def history_undo(self, context):
        if (self.history_idx == 0):
            return
            
        self.history_undo_to_snapshot(context, self.history_idx - 1)
                
    def history_redo(self, context):
        if (self.history_idx == len(self.history) - 1):
            return

        self.history_undo_to_snapshot(context, self.history_idx + 1)
            
        
    def history_restore_bookmark(self, context, bookmark):
        map = self.history[bookmark]
    
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = map[obj]
                
                mesh = obj.data
                bm.to_mesh(mesh)
                mesh.update()
        
    def history_undo_to_snapshot(self, context, idx):
        if idx < 0 or idx >= len(self.history):
            return
            
        self.history_idx = idx
       
        map = self.history[self.history_idx]
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = map[obj]
                
                mesh = obj.data
                bm.to_mesh(mesh)
                mesh.update()
        
    def history_clear(self, context):
        for key in self.history_bookmarks:
            map = self.history_bookmarks[key]
            self.free_snapshot(map)
    
        for map in self.history:
            self.free_snapshot(map)
                
        self.history = []
        self.history_idx = -1
        

    def dab_brush(self, context, event):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        
        targetObj = context.scene.normal_brush_props.target

        ctx = bpy.context

        region = context.region
        rv3d = context.region_data

        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

        viewlayer = bpy.context.view_layer
        result, location, normal, index, object, matrix = ray_cast(context, viewlayer, ray_origin, view_vector)
        
        center = None
        center_count = 0

        selVertsOnly = context.scene.normal_brush_props.selected_verts_only
        selFacesOnly = context.scene.normal_brush_props.selected_faces_only
        radius = context.scene.normal_brush_props.radius
        strength = context.scene.normal_brush_props.strength
        use_pressure = context.scene.normal_brush_props.use_pressure
        brush_type = context.scene.normal_brush_props.brush_type
        brush_normal = context.scene.normal_brush_props.normal
        target = context.scene.normal_brush_props.target
        front_faces_only = context.scene.normal_brush_props.front_faces_only
        sym_x = context.scene.normal_brush_props.symmetry_x
        sym_y = context.scene.normal_brush_props.symmetry_y
        sym_z = context.scene.normal_brush_props.symmetry_z
        

        if result:
            for obj in ctx.selected_objects:
                if obj.type == 'MESH':
                    mesh = obj.data
                    mesh.use_auto_smooth = True
                    
                    mesh.calc_normals_split()

                    #Calc normal for smoothing
                    if brush_type == "SMOOTH":
                        smooth_normal = None
                        
                        for p in mesh.polygons:
                            for loop_idx in p.loop_indices:
                                l = mesh.loops[loop_idx]
                                v = mesh.vertices[l.vertex_index]
                                pos = mathutils.Vector(v.co)
                                wpos = obj.matrix_world @ pos

                                offset = location - wpos
                                if offset.length < radius:
                                    weight = 1 - offset.length / radius
                                    
                                    if smooth_normal == None:
                                        smooth_normal = l.normal * weight
                                    else:
                                        smooth_normal += l.normal * weight
                                    
                        if not smooth_normal == None:
                            smooth_normal.normalize()
                    
                    normals = []
                    
                    for p in mesh.polygons:
                        masked = False
                        if selFacesOnly and not p.select:
                            masked = True
                    
                        for loop_idx in p.loop_indices:
                            l = mesh.loops[loop_idx]
                            
                            v = mesh.vertices[l.vertex_index]
                            if selVertsOnly and not v.select:
                                masked = True
                            
                            pos = mathutils.Vector(v.co)
                            wpos = obj.matrix_world @ pos

                            #Normal transform is (l2w ^ -1) ^ -1 ^ T
                            w2ln = obj.matrix_world.copy()
                            w2ln.transpose()
                            
                            nLocal = None
                            if brush_type == "FIXED":
                                nLocal = brush_normal.to_4d()
                                nLocal.w = 0
                                nLocal = w2ln @ nLocal
                                nLocal = nLocal.to_3d()
                                nLocal.normalize()

                            elif brush_type == "COMB":
                                if len(self.stroke_trail) > 1:
                                    dir = self.stroke_trail[-1] - self.stroke_trail[-2]
                                    if dir.dot(dir) > .0001:
                                        nLocal = w2ln @ dir
                                        nLocal.normalize()

                            elif brush_type == "ATTRACT":
                                if target != None:
                                    m = obj.matrix_world.copy()
                                    m.invert()
                                    targetLoc = m @ target.matrix_world.translation
                                    
                                    nLocal = targetLoc - pos
                                    nLocal.normalize()

                            elif brush_type == "REPEL":
                                if target != None:
                                    m = obj.matrix_world.copy()
                                    m.invert()
                                    targetLoc = m @ target.matrix_world.translation
                                    
                                    nLocal = pos - targetLoc
                                    nLocal.normalize()

                            elif brush_type == "SMOOTH":
                                nLocal = smooth_normal
                                    
                            elif brush_type == "VERTEX":
                                nLocal = mathutils.Vector(v.normal)
                            
                            
                            #Calc new normals (one for each symmetry direction)
                            offsets = [location]
                            norms = [nLocal]
                            view_vecs = [view_vector]
                            
                            if sym_x:
                                offsets = offsets + [mathutils.Vector((-p.x, p.y, p.z)) for p in offsets]
                                norms = norms + [None if p == None else mathutils.Vector((-p.x, p.y, p.z)) for p in norms]
                                view_vecs = view_vecs + [None if p == None else mathutils.Vector((-p.x, p.y, p.z)) for p in view_vecs]
                            
                            if sym_y:
                                offsets = offsets + [mathutils.Vector((p.x, -p.y, p.z)) for p in offsets]
                                norms = norms + [None if p == None else mathutils.Vector((p.x, -p.y, p.z)) for p in norms]
                                view_vecs = view_vecs + [None if p == None else mathutils.Vector((p.x, -p.y, p.z)) for p in view_vecs]
                            
                            if sym_z:
                                offsets = offsets + [mathutils.Vector((p.x, p.y, -p.z)) for p in offsets]
                                norms = norms + [None if p == None else mathutils.Vector((p.x, p.y, -p.z)) for p in norms]
                                view_vecs = view_vecs + [None if p == None else mathutils.Vector((p.x, p.y, -p.z)) for p in view_vecs]
                            
                            
                            rot_to = []
                            
                            for loc, norm, view_vec in zip(offsets, norms, view_vecs):
                            
                                offset = loc - wpos
                                t = 1 - offset.length / radius
        
                                vv = view_vec.to_4d()
                                vv.w = 0
                                view_local = w2ln @ vv
                                view_local = view_local.to_3d()
                                
                                if t <= 0 or norm == None or (p.normal.dot(view_local) > 0 and front_faces_only) or masked:
                                    pass
                                else:
                                    axis = l.normal.cross(norm)
                                    angle = norm.angle(l.normal)
                                    
                                    atten = strength
                                    if use_pressure:
                                        atten *= event.pressure
                                    
                                    q = mathutils.Quaternion(axis, angle * t * atten)
                                    m = q.to_matrix()
                                    
                                    newNorm = m @ l.normal
                                    
                                    rot_to.append(newNorm)
                                    
                            #Apply average new normal to mesh
                            if len(rot_to) == 0:
                                normals.append(l.normal)
                            elif len(rot_to) == 1:
                                normals.append(rot_to[0])
                            else:
                                merged_norm = mathutils.Vector(rot_to[0])
                                for v in rot_to[1:]:
                                    merged_norm = merged_norm + v
                                merged_norm.normalize()
                                normals.append(merged_norm)
                                
                        
                    mesh.normals_split_custom_set(normals)

            self.stroke_trail.append(location)
            
        else:
            self.stroke_trail = []
        

    def mouse_move(self, context, event):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        ctx = bpy.context

        region = context.region
        rv3d = context.region_data

        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

        viewlayer = bpy.context.view_layer
        result, location, normal, index, object, matrix = ray_cast(context, viewlayer, ray_origin, view_vector)
        
        #Brush cursor display
        if result:
            self.show_cursor = True
            self.cursor_pos = location
            self.cursor_normal = normal
            self.cursor_object = object
            self.cursor_matrix = matrix
        else:
            self.show_cursor = False

        if self.dragging:
            self.dab_brush(context, event)


    def mouse_down(self, context, event):
        if event.value == "PRESS":
            
            mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            region = context.region
            rv3d = context.region_data

            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
            ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

            viewlayer = bpy.context.view_layer
            result, location, normal, index, object, matrix = ray_cast(context, viewlayer, ray_origin, view_vector)

            if result == False or object.select_get() == False:
                return {'PASS_THROUGH'}
                            
            self.dragging = True
            self.stroke_trail = []
            
            self.dab_brush(context, event)
            
        elif event.value == "RELEASE":
            self.dragging = False
            self.history_snapshot(context)


        return {'RUNNING_MODAL'}
    

    def modal(self, context, event):
        redraw_all_viewports(context)
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}

        elif event.type == 'MOUSEMOVE':
            self.mouse_move(context, event)
            
            if self.dragging:
                return {'RUNNING_MODAL'}
            else:
                return {'PASS_THROUGH'}
            
        elif event.type == 'LEFTMOUSE':
            return self.mouse_down(context, event)

        elif event.type in {'Z'}:
            if event.ctrl:
                if event.shift:
                    if event.value == "RELEASE":
                        self.history_redo(context)
                    return {'RUNNING_MODAL'}
                else:
                    if event.value == "RELEASE":
                        self.history_undo(context)

                    return {'RUNNING_MODAL'}
                
            return {'RUNNING_MODAL'}
        
        elif event.type in {'RET'}:
            if event.value == 'RELEASE':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self.history_clear(context)
                return {'FINISHED'}
            return {'RUNNING_MODAL'}

        elif event.type in {'PAGE_UP', 'RIGHT_BRACKET'}:
            if event.value == "PRESS":
                brush_radius = context.scene.normal_brush_props.radius
                brush_radius = brush_radius + .1
                context.scene.normal_brush_props.radius = brush_radius
            return {'RUNNING_MODAL'}

        elif event.type in {'PAGE_DOWN', 'LEFT_BRACKET'}:
            if event.value == "PRESS":
                brush_radius = context.scene.normal_brush_props.radius
                brush_radius = max(brush_radius - .1, .1)
                context.scene.normal_brush_props.radius = brush_radius
            return {'RUNNING_MODAL'}
            
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if event.value == 'RELEASE':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self.history_restore_bookmark(context, 0)
                self.history_clear(context)            
                return {'CANCELLED'}
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._context = context
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, args, 'WINDOW', 'POST_VIEW')

            redraw_all_viewports(context)
            self.history_clear(context)
            self.history_snapshot(context)
            self.history_snapshot(context, 0)

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

#---------------------------

class NormalPickerOperator(bpy.types.Operator):
    """Pick normal"""
    bl_idname = "kitfox.nt_pick_normal"
    bl_label = "Pick Normal"
    bl_options = {"REGISTER", "UNDO"}
    
    def __init__(self):
        self.picking = False

    def mouse_down(self, context, event):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        ctx = bpy.context

        region = context.region
        rv3d = context.region_data

        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)


        viewlayer = bpy.context.view_layer
        result, location, normal, index, object, matrix = ray_cast(context, viewlayer, ray_origin, view_vector)
        
        if result:
            context.scene.normal_brush_props.normal = normal
            redraw_all_viewports(context)


    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            if self.picking:
                context.window.cursor_set("EYEDROPPER")
            else:
                context.window.cursor_set("DEFAULT")
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE':
            self.picking = False
            self.mouse_down(context, event)
#            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.window.cursor_set("DEFAULT")
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.picking = False
#            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            print("pick target object cancelled")
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':

            args = (self, context)
            self._context = context

            context.window_manager.modal_handler_add(self)
            
            context.window.cursor_set("EYEDROPPER")
            self.picking = True
            
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

#---------------------------


class NormalToolPropsPanel(bpy.types.Panel):

    """Properties Panel for the Normal Tool on tool shelf"""
    bl_label = "Normal Brush"
    bl_idname = "OBJECT_PT_normal_tool_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
#    bl_context = "objectmode"
    bl_category = "Kitfox - Normal"


    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj != None and (obj.mode == 'OBJECT')
#        return obj != None and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        settings = scene.normal_brush_props
        
        pcoll = preview_collections["main"]
        
        
        col = layout.column();
        col.operator("kitfox.normal_tool", text="Start Normal Tool", icon_value = pcoll["normalTool"].icon_id)
        
        col.prop(settings, "strength")
        col.prop(settings, "use_pressure")
        col.prop(settings, "normal_length")
        col.prop(settings, "radius")
        col.prop(settings, "front_faces_only")
#        col.prop(settings, "selected_verts_only")
        col.prop(settings, "selected_faces_only")

        col.label(text="Brush Type:")
        col.prop(settings, "brush_type", expand = True)
#        row = layout.col();
#        row.prop(settings, "brush_type", expand = True)

        col = layout.column();
        brush_type = context.scene.normal_brush_props.brush_type

        col.label(text="Symmetry:")
        row = layout.row();
        row.prop(settings, "symmetry_x", text = "X", toggle = True)
        row.prop(settings, "symmetry_y", text = "Y", toggle = True)
        row.prop(settings, "symmetry_z", text = "Z", toggle = True)

        if brush_type == "FIXED":
            col = layout.column();
            if not context.scene.normal_brush_props.normal_exact:
                col.label(text="Normal:")
                col.prop(settings, "normal", text="")
            else:
                col.prop(settings, "normal", expand = True)
            col.prop(settings, "normal_exact")
            col.operator("kitfox.nt_pick_normal", icon="EYEDROPPER")
            
        elif brush_type == "ATTRACT" or brush_type == "REPEL":
            col = layout.column();
            col.prop(settings, "target")
        

#---------------------------

preview_collections = {}

def register():

    bpy.utils.register_class(NormalToolSettings)
    bpy.utils.register_class(NormalPickerOperator)
    bpy.utils.register_class(ModalDrawOperator)
    bpy.utils.register_class(NormalToolPropsPanel)

    bpy.types.Scene.normal_brush_props = bpy.props.PointerProperty(type=NormalToolSettings)

    #Load icons
    icon_path = "../icons"
    if __name__ == "__main__":
        icon_path = "../../source/icons"
        
    icons_dir = os.path.join(os.path.dirname(__file__), icon_path)
    
    print("icons dir: " + str(icons_dir))
    
    pcoll = bpy.utils.previews.new()
    pcoll.load("normalTool", os.path.join(icons_dir, "normalTool.png"), 'IMAGE')
    preview_collections["main"] = pcoll


def unregister():
    bpy.utils.unregister_class(NormalToolSettings)
    bpy.utils.unregister_class(NormalPickerOperator)
    bpy.utils.unregister_class(ModalDrawOperator)
    bpy.utils.unregister_class(NormalToolPropsPanel)

    del bpy.types.Scene.normal_brush_props
    
    #Unload icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    


if __name__ == "__main__":
    register()

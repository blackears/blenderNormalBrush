#Copyright 2021 Mark McKay
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.


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


class NormalToolSettings(bpy.types.PropertyGroup):
    brush_type : bpy.props.EnumProperty(
        items=(
            ('FIXED', "Fixed", "Normals are in a fixed direction"),
            ('COMB', "Comb", "Normals point in the direction that the brush moves"),
            ('ATTRACT', "Attract", "Normals point toward target object"),
            ('REPEL', "Repel", "Normals point away from target object"),
            ('VERTEX', "Vertex", "Get normal values from mesh vertices")
        ),
        default='FIXED'
    )
    
    radius : bpy.props.FloatProperty(
        name="Radius", description="Radius of brush", default = 1, min=0, soft_max = 4
    )
    
    strength : bpy.props.FloatProperty(
        name="Strength", description="Amount to adjust mesh normal", default = 1, min=0, max = 1
    )

    use_pressure : bpy.props.BoolProperty(
        name="Pen Pressure", description="If true, pen pressure is used to adjust strength", default = True
    )
    
    normal_length : bpy.props.FloatProperty(
        name="Normal Length", description="Display length of normal", default = 1, min=0, soft_max = 1
    )

    selected_only : bpy.props.BoolProperty(
        name="Selected Only", description="If true, affect only selected vertices", default = True
    )

    normal : bpy.props.FloatVectorProperty(
        name="Normal", 
        description="Direction of normal in Fixed mode", 
        default = (1, 0, 0), 
        subtype="DIRECTION"
    )
    
    normal_exact : bpy.props.BoolProperty(
        name="Exact normal", description="Display normal as exact coordinates", default = True
    )

    
    front_faces_only : bpy.props.BoolProperty(
        name="Front Faces Only", description="Only affect normals on front facing faces", default = True
    )

    target : bpy.props.PointerProperty(name="Target", description="Object Attract and Repel mode reference", type=bpy.types.Object)
    

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
    norm = normal.copy()
    norm.resize_4d()
    norm.w = 0
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


    # shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    # batchLine = batch_for_shader(shader, 'LINES', {"pos": coordsNormal})
    # batchCircle = batch_for_shader(shader, 'LINE_STRIP', {"pos": coordsCircle})

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


    selOnly = context.scene.normal_brush_props.selected_only

    normLength = context.scene.normal_brush_props.normal_length
    mS = mathutils.Matrix.Scale(normLength, 4)

    for obj in ctx.selected_objects:
        if obj.type == 'MESH':
            success = obj.update_from_editmode()
            mesh = obj.data

    
            mesh.calc_normals_split()
            
            for l in mesh.loops:
                    
                v = mesh.vertices[l.vertex_index]
                m = calc_vertex_transform(obj, v.co, l.normal)
                m = m @ mS

        
                gpu.matrix.push()
                
                gpu.matrix.multiply_matrix(m)
                shader.uniform_float("color", (1, 1, 0, 1))
                batchLine.draw(shader)
                
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
#        result, location, normal, index, object, matrix = context.scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)
        
        center = None
        center_count = 0

        selOnly = context.scene.normal_brush_props.selected_only
        radius = context.scene.normal_brush_props.radius
        strength = context.scene.normal_brush_props.strength
        use_pressure = context.scene.normal_brush_props.use_pressure
        brush_type = context.scene.normal_brush_props.brush_type
        brush_normal = context.scene.normal_brush_props.normal
        target = context.scene.normal_brush_props.target
        front_faces_only = context.scene.normal_brush_props.front_faces_only
        

        if result:
        
            for obj in ctx.selected_objects:
                if obj.type == 'MESH':
                    mesh = obj.data
                    mesh.use_auto_smooth = True
                    
                    mesh.calc_normals_split()
                    
                    normals = []
                    
                    for p in mesh.polygons:
                        for loop_idx in p.loop_indices:
                            l = mesh.loops[loop_idx]
                            
                            v = mesh.vertices[l.vertex_index]
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
                                    
                            elif brush_type == "VERTEX":
                                nLocal = mathutils.Vector(v.normal)
                            
                            
                            offset = location - wpos
                            t = 1 - offset.length / radius
    
                            view_local = w2ln @ view_vector
                            
                            
                            if t <= 0 or nLocal == None or (p.normal.dot(view_local) > 0 and front_faces_only):
                                normals.append(l.normal)
                            else:
                                axis = l.normal.cross(nLocal)
                                angle = nLocal.angle(l.normal)
                                
                                atten = strength
                                if use_pressure:
                                    atten *= event.pressure
                                
                                q = mathutils.Quaternion(axis, angle * t * atten)
                                m = q.to_matrix()
                                
                                newNorm = m @ l.normal
                                
                                normals.append(newNorm)
                        
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
#        result, location, normal, index, object, matrix = context.scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)
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

        context.area.tag_redraw()

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

            context.area.tag_redraw()
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
    picking = False

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
            context.area.tag_redraw()


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
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.window.cursor_set("DEFAULT")
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.picking = False
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            print("pick target object cancelled")
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._context = context
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, args, 'WINDOW', 'POST_VIEW')

            context.window_manager.modal_handler_add(self)
            
            context.window.cursor_set("EYEDROPPER")
            self.picking = True
            
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

#---------------------------

class NormalToolPanel(bpy.types.Panel):

    """Panel for the Normal Tool on tool shelf"""
    bl_label = "Normal Tool Panel"
    bl_idname = "OBJECT_PT_normal_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.operator("kitfox.normal_tool")

#---------------------------


class NormalToolPropsPanel(bpy.types.Panel):

    """Properties Panel for the Normal Tool on tool shelf"""
    bl_label = "Normal Brush"
    bl_idname = "OBJECT_PT_normal_tool_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = "Kitfox"

        

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

        row = layout.row();
        row.prop(settings, "brush_type", expand = True)

        col = layout.column();
        brush_type = context.scene.normal_brush_props.brush_type

        if brush_type == "FIXED":
            if not context.scene.normal_brush_props.normal_exact:
                col.label(text="Normal:")
                col.prop(settings, "normal", text="")
            else:
                col.prop(settings, "normal", expand = True)
            col.prop(settings, "normal_exact")
            col.operator("kitfox.nt_pick_normal", icon="EYEDROPPER")
            
        elif brush_type == "ATTRACT" or brush_type == "REPEL":
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

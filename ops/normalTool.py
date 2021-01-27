import bpy
import bmesh
import bgl
import blf
import gpu
import mathutils
import math
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils



class NormalToolSettings(bpy.types.PropertyGroup):
    brush_type : bpy.props.EnumProperty(
        items=(
            ('FIXED', "Fixed", "Normals are in a fixed direction"),
            ('ATTRACT', "Attract", "Normals point toward target object"),
            ('REPEL', "Repel", "Normals point away from target object")
        ),
        default='FIXED'
    )
    
    radius : bpy.props.FloatProperty(
        name="Radius", description="Radius of brush", default = 1, min=0, soft_max = 4
    )
    
    strength : bpy.props.FloatProperty(
        name="Strength", description="Amount to adjust mesh normal", default = 1, min=0, max = 1
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
        name="Exact normal", description="Display normal as exact coordinates", default = False
    )

    target : bpy.props.PointerProperty(name="Target", description="Object Attract and Repel mode reference", type=bpy.types.Object)
        

#---------------------------
        

circleSegs = 64
coordsCircle = [(math.sin(((2 * math.pi * i) / circleSegs)), math.cos((math.pi * 2 * i) / circleSegs), 0) for i in range(circleSegs + 1)]

coordsNormal = [(0, 0, 0), (0, 0, 1)]

vecZ = mathutils.Vector((0, 0, 1))
vecX = mathutils.Vector((1, 0, 0))


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
#                    print (quat)
    mR = quat.to_matrix()
#                    print (mR)
    mR.resize_4x4()
#                    print (mR)
    
    mT = mathutils.Matrix.Translation(pos)
#                    print (mT)

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
#    print("draw_callback_px");
    ctx = bpy.context

    region = context.region
    rv3d = context.region_data
#    coord = event.mouse_region_x, event.mouse_region_y

    viewport_center = (region.x + region.width / 2, region.y + region.height / 2)
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, viewport_center)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, viewport_center)

    # get the ray from the viewport and mouse
#    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
#    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)


    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coordsNormal})
    batchCircle = batch_for_shader(shader, 'LINE_STRIP', {"pos": coordsCircle})

    shader.bind();
    
    #Draw cursor
    if self.show_cursor:
#        m = calc_vertex_transform(self.cursor_object, self.cursor_pos, self.cursor_normal);
#        m = self.cursor_matrix
        m = calc_vertex_transform_world(self.cursor_pos, self.cursor_normal);

        gpu.matrix.push()
        
        gpu.matrix.multiply_matrix(m)
        shader.uniform_float("color", (1, 0, 1, 1))
        batch.draw(shader)

        shader.uniform_float("color", (1, 0, 1, 1))
        batchCircle.draw(shader)
        
        gpu.matrix.pop()

    
    #Draw editable normals
    shader.uniform_float("color", (1, 1, 0, 1))


    selOnly = context.scene.my_tool.selected_only

    normLength = context.scene.my_tool.normal_length
    mS = mathutils.Matrix.Scale(normLength, 4)

    for obj in ctx.selected_objects:
        if obj.type == 'MESH':
            success = obj.update_from_editmode()
            mesh = obj.data

    
#            bm = bmesh.new()
#            bm.from_mesh(mesh)
#            for v in bm.verts:
#bm.to_mesh(me)
#bm.free()
            mesh.calc_normals_split()
            
            for l in mesh.loops:

#            for v in mesh.vertices:
                if not (selOnly and not v.select):
                    
#                    m = calc_gizmo_transform(obj, v.co, v.normal, ray_origin)
                    v = mesh.vertices[l.vertex_index]
                    m = calc_vertex_transform(obj, v.co, l.normal)
                    m = m @ mS

            
                    gpu.matrix.push()
                    
                    gpu.matrix.multiply_matrix(m)
                    shader.uniform_float("color", (1, 1, 0, 1))
                    batch.draw(shader)
                    
#                    gpu.matrix.push()
#                    gpu.matrix.multiply_matrix(mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Y'))
#                    shader.uniform_float("color", (1, 0, 0, 1))
#                    batchCircle.draw(shader)
#                    gpu.matrix.pop()
#                    
#                    gpu.matrix.push()
#                    gpu.matrix.multiply_matrix(mathutils.Matrix.Rotation(math.radians(90.0), 4, 'X'))
#                    shader.uniform_float("color", (0, 1, 0, 1))
#                    batchCircle.draw(shader)
#                    gpu.matrix.pop()

#                    shader.uniform_float("color", (0, 0, 1, 1))
#                    batchCircle.draw(shader)
#                    
                    gpu.matrix.pop()


def manip_normal(context, event):
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

    ray_target = ray_origin + view_vector


#---------------------------

class ModalDrawOperator(bpy.types.Operator):
    """Adjust normals"""
    bl_idname = "kitfox.normal_tool"
    bl_label = "Normal Tool Kitfox"


#    prop_brush_type : bpy.props.EnumProperty(
#        items=(
#            ('FIXED', "Fixed", "Normals are in a fixed direction"),
#            ('ATTRACT', "Attract", "Normals point toward target object"),
#            ('REPEL', "Repel", "Normals point away from target object")
#        ),
#        default='FIXED'
#    )
#    
#    prop_strength : bpy.props.FloatProperty(
#        name="Strength", description="Amount to adjust mesh normal", default = 1, min=0, max = 1
#    )

#    prop_normal : bpy.props.FloatVectorProperty(name="Normal", description="Direction of normal in Fixed mode", default = (0, 1, 0))
#    prop_target : bpy.props.StringProperty(name="Target", description="Object Attract and Repel mode reference", default="")
#    
    dragging = False
    
    cursor_pos = None
    show_cursor = False
    
    bm = None

    def mouse_move(self, context, event):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        ctx = bpy.context

        region = context.region
        rv3d = context.region_data

        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

        viewlayer = bpy.context.view_layer
        result, location, normal, index, object, matrix = context.scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)
        
        
        if result:
            self.show_cursor = True
            self.cursor_pos = location
            self.cursor_normal = normal
            self.cursor_object = object
            self.cursor_matrix = matrix
        else:
            self.show_cursor = False


    def mouse_down(self, context, event):
        if event.value == "PRESS":
            self.dragging = True
        elif event.value == "RELEASE":
            self.dragging = False
            return;
            
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        
#        print("Foobar--")

#        context.scene.my_tool.target = hit_object
        targetObj = context.scene.my_tool.target
#        if targetObj != None:
#            print("^^^Tool property target: " + targetObj.name)
#        else:
#            print("^^^Tool property target: None")

        ctx = bpy.context

        region = context.region
        rv3d = context.region_data
    #    coord = event.mouse_region_x, event.mouse_region_y

#        viewport_center = (region.x + region.width / 2, region.y + region.height / 2)
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

        viewlayer = bpy.context.view_layer
        result, location, normal, index, object, matrix = context.scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)
        
        center = None
        center_count = 0

        selOnly = context.scene.my_tool.selected_only
        brush_normal = context.scene.my_tool.normal
        radius = context.scene.my_tool.radius
        strength = context.scene.my_tool.strength

        if result:

        #---
        #This works, but only in object mode
#        success = obj.update_from_editmode()
        
            for obj in ctx.selected_objects:
                if obj.type == 'MESH':
    #                print("Updating mesh " + obj.name)
                    mesh = obj.data
                    mesh.use_auto_smooth = True
                    
                    mesh.calc_normals_split()
                    
                    normals = []
                    for l in mesh.loops:
#                        normals.append(brush_normal)
                        
                        v = mesh.vertices[l.vertex_index]
                        pos = mathutils.Vector(v.co)
                        wpos = obj.matrix_world @ pos
                        
                        offset = location - wpos
#                        offset.length_squared / radius * radius
                        t = 1 - offset.length / radius
                        
                        if t <= 0:
                            normals.append(l.normal)
                        else:
                            axis = l.normal.cross(brush_normal)
                            angle = brush_normal.angle(l.normal)
                            q = mathutils.Quaternion(axis, angle * t * strength)
                            m = q.to_matrix()
                            
                            newNorm = m @ l.normal
                            
                            normals.append(newNorm)
                    
                    mesh.normals_split_custom_set(normals)
                    
                    
#                    mesh.normals_split_custom_set([(0, 0, 0) for l in mesh.loops])
#                    
#                    normals = []
#                    for v in mesh.vertices:
#                        normals.append(brush_normal)

#                    mesh.normals_split_custom_set_from_vertices(normals)



#        me = context.edit_object.data
#        me.use_auto_smooth = True
#        
#        self.bm = bmesh.from_edit_mesh(me)

##        print("updating faces")
#        for face in self.bm.faces:
#            for loop in face.loops:
##                print("-face norm " + str(loop.vert.normal))
#                loop.vert.normal = brush_normal
##                loop.vert.co[0] = loop.vert.co[0] + .1
##                
#        me = context.edit_object.data
#        bmesh.update_edit_mesh(me, False, False)





#        for obj in ctx.selected_objects:
#            if obj.type == 'MESH':
#                print("Updating mesh " + obj.name)
                
#                me = obj.data
#                bm = bmesh.new()
#                bm.from_mesh(mesh)
#                bm = bmesh.from_edit_mesh(me)
                
#                for face in self.bm.faces:
#                    for loop in face.loops:
##                        loop.vert
#                        loop.vert.normal = brush_normal
#                        
#                me = context.edit_object.data
#                bmesh.update_edit_mesh(me, False, False)
#                
#                bm.to_mesh(mesh)
#                bm.free()
                
#                success = obj.update_from_editmode()
#                print ("Update from editr mode success: " + success)


                
                
                
                #----


                
#                for v in mesh.vertices:
#                    if not (selOnly and not v.select):
#                        if center_count == 0:
#                            center = v.co
#                        else:
#                            center += v.co
#                        center_count += 1
#                        
#                        m = calc_gizmo_transform(obj, v.co, v.normal, ray_origin)


        self.drag_start_pos = mouse_pos
            
        pass

    def modal(self, context, event):
        
        
            
    
#        self._context = context

#        for obj in context.selected_objects:
#            if obj.type == 'MESH':
#                mesh = obj.data
#                success = mesh.update_from_editmode()
            
        context.area.tag_redraw()

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}

        elif event.type == 'MOUSEMOVE':
            self.mouse_move(context, event)
            return {'RUNNING_MODAL'}
            
        elif event.type == 'LEFTMOUSE':
            self.mouse_down(context, event)
            return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            print("norm tool cancelled")
            return {'CANCELLED'}

        return {'PASS_THROUGH'}
#        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._context = context
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, args, 'WINDOW', 'POST_VIEW')

            self.mouse_path = []

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

#---------------------------

class NormalPickerOperator(bpy.types.Operator):
    """Pick normal"""
    bl_idname = "kitfox.nt_pick_normal"
    bl_label = " Pick Normal"

    def mouse_down(self, context, event):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        ctx = bpy.context

        region = context.region
        rv3d = context.region_data

        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)


        viewlayer = bpy.context.view_layer
        result, location, normal, index, object, matrix = context.scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)
        
        if result:
            print("--picked " + str(normal))
            context.scene.my_tool.normal = normal
            context.area.tag_redraw()


    def modal(self, context, event):
        if event.type == 'LEFTMOUSE':
            self.mouse_down(context, event)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            print("pick target object cancelled")
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
#    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.operator("kitfox.normal_tool")

#---------------------------

class NormalToolPropsPanel(bpy.types.Panel):

    """Properties Panel for the Normal Tool on tool shelf"""
    bl_label = "Normal Tool Properties Panel"
    bl_idname = "OBJECT_PT_normal_tool_props"
    bl_space_type = 'VIEW_3D'
#    bl_region_type = 'TOOL_PROPS'
    bl_region_type = 'UI'
#    bl_context = "object"
    bl_category = "Kitfox"

        

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        settings = scene.my_tool
        
        col = layout.column();
        col.prop(settings, "strength")
        col.prop(settings, "normal_length")
        col.prop(settings, "selected_only")

        row = layout.row();
        row.prop(settings, "brush_type", expand = True)

        col = layout.column();
#                    context.scene.my_tool.normal = normal

        if str(context.scene.my_tool.brush_type) == "FIXED":
            if not context.scene.my_tool.normal_exact:
                col.label(text="Normal:")
                col.prop(settings, "normal", text="")
            else:
                col.prop(settings, "normal", expand = True)
            col.prop(settings, "normal_exact")
            col.operator("kitfox.nt_pick_normal", icon="EYEDROPPER")
        else:
            col.prop(settings, "target")
        

#---------------------------


def register():

    bpy.utils.register_class(NormalToolSettings)
    bpy.utils.register_class(NormalPickerOperator)
    bpy.utils.register_class(ModalDrawOperator)
    bpy.utils.register_class(NormalToolPanel)
    bpy.utils.register_class(NormalToolPropsPanel)

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=NormalToolSettings)


def unregister():
    bpy.utils.unregister_class(NormalToolSettings)
    bpy.utils.unregister_class(NormalPickerOperator)
    bpy.utils.unregister_class(ModalDrawOperator)
    bpy.utils.unregister_class(NormalToolPanel)
    bpy.utils.unregister_class(NormalToolPropsPanel)

    del bpy.types.Scene.my_tool
    


if __name__ == "__main__":
    register()

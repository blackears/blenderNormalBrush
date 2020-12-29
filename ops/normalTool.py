import bpy
import bgl
import blf
import gpu
import mathutils
import math
from gpu_extras.batch import batch_for_shader



def draw_callback(self, context):
#    print("draw_callback_px");
    ctx = bpy.context
    
#    coords = [(1, 1, 1), (-2, 0, 0), (-2, -1, 3), (0, 1, 1)]
    coords = [(0, 0, 0), (0, 0, 1)]
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords})

    shader.bind();
    shader.uniform_float("color", (1, 1, 0, 1))

#    batch.draw(shader)
    vecZ = mathutils.Vector((0, 0, 1))
    vecX = mathutils.Vector((1, 0, 0))

#    bpy.context.scene.update()

    for obj in ctx.selected_objects:
#    for obj in context.scene.objects:
        if obj.type == 'MESH':
            mesh = obj.data
            mesh.update()

            gpu.matrix.push()
            gpu.matrix.multiply_matrix(obj.matrix_world)
    
#            bm = bmesh.new()
#            bm.from_mesh(mesh)
#            for v in bm.verts:
#bm.to_mesh(me)
#bm.free()

            for v in mesh.vertices:
                if v.select:
#                    v.co
                    axis = v.normal.cross(vecZ)
                    if axis.length_squared < .0001:
                        axis = matutils.Vector(vecX)
                    else:
                        axis.normalize()
                    angle = -math.acos(v.normal.dot(vecZ))
                    
                    quat = mathutils.Quaternion(axis, angle)
#                    print (quat)

                    mR = quat.to_matrix()
#                    print (mR)
                    mR.resize_4x4()
#                    print (mR)
                    
                    mT = mathutils.Matrix.Translation(v.co)
#                    print (mT)

                    m = mT @ mR
#                    m = mT
#                    print (m)
                    
#                    binorm = v.normal.cross(tan)
                    batchAxis = batch_for_shader(shader, 'LINES', {"pos": [v.co, v.co + axis]})
                    shader.uniform_float("color", (1, 0, 1, 1))
                    batchAxis.draw(shader)

            
                    gpu.matrix.push()
                    gpu.matrix.multiply_matrix(m)
                    shader.uniform_float("color", (1, 1, 0, 1))
                    batch.draw(shader)
                    gpu.matrix.pop()

            gpu.matrix.pop()

#    print("mouse points", len(self.mouse_path))

#    font_id = 0  # XXX, need to find out how best to get this.

    # draw some text
#    blf.position(font_id, 15, 30, 0)
#    blf.size(font_id, 20, 72)
#    blf.draw(font_id, "Hello Word " + str(len(self.mouse_path)))

    # 50% alpha, 2 pixel width line
#    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
#    bgl.glEnable(bgl.GL_BLEND)
#    bgl.glLineWidth(2)
#    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": self.mouse_path})
#    shader.bind()
#    shader.uniform_float("color", (0.0, 0.0, 0.0, 0.5))
#    batch.draw(shader)

    # restore opengl defaults
#    bgl.glLineWidth(1)
#    bgl.glDisable(bgl.GL_BLEND)


class ModalDrawOperator(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "view3d.normal_tool"
    bl_label = "Normal Tool Kitfox"

    def modal(self, context, event):
        self._context = context
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
#            self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))
            pass

        elif event.type == 'LEFTMOUSE':
#            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
#            return {'FINISHED'}
            pass

#        elif event.type in {'RIGHTMOUSE', 'ESC'}:
        elif event.type in {'ESC'}:
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


def register():
    bpy.utils.register_class(ModalDrawOperator)


def unregister():
    bpy.utils.unregister_class(ModalDrawOperator)


if __name__ == "__main__":
    register()

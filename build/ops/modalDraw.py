import bpy
import bgl
import blf
import gpu
import numpy as np


g_vertSrc = '''
uniform mat4 viewproj;

in vec3 pos;

void main()
{
	gl_Position = viewproj * vec4(pos, 1.0);
}

'''

g_fragSrc = '''
uniform vec4 color;

out vec4 fragColor;

void main()
{
	fragColor = color;
}
'''
g_plane_vertices = np.array([ ([0.5, 0.5, 0]),], [('pos', 'f4', 3)])

class SnapDrawn():
    def __init__(self):
        self._format = gpu.types.GPUVertFormat()
        self._pos_id = self._format.attr_add(
                id = "pos",
                comp_type = "F32",
                len = 3,
                fetch_mode = "FLOAT")

        self.shader = gpu.types.GPUShader(g_vertSrc, g_fragSrc)
        self.unif_color = self.shader.uniform_from_name("color")
        self.color = np.array([1.0, 0.8, 0.0, 0.5], 'f')
        
        self.per_mat = self.shader.uniform_from_name("viewproj")


    def batch_line_strip_create(self, coords):
        global g_plane_vertices
        vbo = gpu.types.GPUVertBuf(len = len(g_plane_vertices), format = self._format)
        vbo.fill(id = self._pos_id, data = g_plane_vertices)

        batch_lines = gpu.types.GPUBatch(type = "POINTS", buf = vbo)
        #batch_lines.program_set_builtin(id = "2D_UNIFORM_COLOR")
        batch_lines.program_set(self.shader)

        return batch_lines


    def draw(self, list_verts_co, rv3d):
        

        batch = self.batch_line_strip_create(list_verts_co)

        #batch.uniform_f32("color", 1.0, 0.8, 0.0, 0.5)
        self.shader.uniform_vector_float(self.unif_color, self.color, 4)
        
        
       
        viewproj = np.array(rv3d.perspective_matrix.transposed(), 'f')
        self.shader.bind()
        self.shader.uniform_vector_float(self.per_mat, viewproj, 16)
        
        batch.draw()
        del batch


def draw_callback_px(self, context):
    print("mouse points", len(self.mouse_path))

    font_id = 0  # XXX, need to find out how best to get this.

    # draw some text
    blf.position(font_id, 15, 30, 0)
    blf.size(font_id, 20, 72)
    blf.draw(font_id, "Hello Word " + str(len(self.mouse_path)))

    # 50% alpha, 2 pixel width line
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(2.0)

    self.snap_draw.draw(self.mouse_path, self.rv3d)

    #restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)


class ModalDrawOperator(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "view3d.modal_operator"
    bl_label = "Simple Modal View3D Operator"
    
    global_shader = None
    unif_viewproj = -1
   
    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

        elif event.type == 'LEFTMOUSE':
            del self.snap_draw
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            del self.snap_draw
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            self.rv3d = context.region_data
           
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.mouse_path = []
            self.snap_draw = SnapDrawn()

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
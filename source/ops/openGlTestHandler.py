import bpy
import bgl
import blf

import math


# I am using the driver namespace as a quick method of global persistent storage.
namespace = bpy.app.driver_namespace


def scribble(text, x, y, px=12, pivot=(0.5, 0.0), rotation=0.0):
    blf.enable(0, blf.ROTATION)
    
    blf.size(0, px, 72)
    
    dimensions = blf.dimensions(0, text)
    
    sin = math.sin(rotation)
    cos = math.cos(rotation)
    
    offset = (
        dimensions[0] * pivot[0] * cos - dimensions[1] * pivot[1] * sin,
        dimensions[0] * pivot[0] * sin + dimensions[1] * pivot[1] * cos
    )
    
    position = (x - offset[0], y - offset[1])
    
    blf.position(0, position[0], position[1], 0.0)
    blf.rotation(0, rotation)
    
    blf.draw(0, text)
    
    blf.disable(0, blf.ROTATION)


vertex_shader_source = """
    #version 330
    
    in vec3 point;
    in vec4 color;
    
    uniform mat4 perspective;
    
    out VertexOut
    {
        vec4 color;
    } vs_out;
    
    void main()
    {
        gl_Position = perspective * vec4(point, 1.0);
        vs_out.color = color;
    }
"""

fragment_shader_source = """
    #version 330
    
    in VertexOut
    {
        vec4 color;
    } fs_in;
    
    out vec4 fragColor;
    
    void main()
    {
        fragColor = fs_in.color;
    }
"""

def draw_pixel():
    scribble("This is text in 2D space.", 100, 100)


def draw_view():
    
    ######################
    ######## BIND ########
    ######################
    
    first_time = not bgl.glIsVertexArray(namespace['vao'][0])
    
    if first_time:
        namespace['uniform_set'] = False
        
        # Unlike VBOs, a VAO has to be generated and deleted from within the draw callback in which it will be bound.
        bgl.glGenVertexArrays(1, namespace['vao'])
        bgl.glBindVertexArray(namespace['vao'][0])
        
        float_byte_count = 4
        
        # Attribute: "point", 3D float vector
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, namespace['vbo_point'][0])
        bgl.glBufferData(bgl.GL_ARRAY_BUFFER, len(namespace['data_point']) * float_byte_count, namespace['data_point'], bgl.GL_DYNAMIC_DRAW)
        
        bgl.glVertexAttribPointer(0, 3, bgl.GL_FLOAT, bgl.GL_FALSE, 0, None)
        bgl.glEnableVertexAttribArray(0)
        
        # Attribute: "color", 4D float vector
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, namespace['vbo_color'][0])
        bgl.glBufferData(bgl.GL_ARRAY_BUFFER, len(namespace['data_color']) * float_byte_count, namespace['data_color'], bgl.GL_DYNAMIC_DRAW)
        
        bgl.glVertexAttribPointer(1, 4, bgl.GL_FLOAT, bgl.GL_FALSE, 0, None)
        bgl.glEnableVertexAttribArray(1)
        
        bgl.glBindVertexArray(0)
    
    ######################
    ######## DRAW ########
    ######################
    
    bgl.glEnable(bgl.GL_BLEND)
    
    bgl.glUseProgram(namespace['shader_program'])
    
    if not namespace['uniform_set']:
        bgl.glUniformMatrix4fv(
            namespace['perspective_uniform_location'],
            1,
            bgl.GL_TRUE, # Matrices in Blender are row-major while matrices in OpenGL are column-major, so Blender's perspective matrix has to be transposed for OpenGL.
            namespace['projection_matrix'])
        
        # In this case I only want to update the uniform once, even though namespace['projection_matrix'] is being updated constantly.
        namespace['uniform_set'] = True
    
    bgl.glBindVertexArray(namespace['vao'][0])
    bgl.glDrawArrays(bgl.GL_TRIANGLES, 0, 3)
    
    bgl.glUseProgram(0)
    bgl.glBindVertexArray(0)
    
    bgl.glDisable(bgl.GL_BLEND)


class WM_OT_opengl_test(bpy.types.Operator):
    """To use this operator, run this script and type "OpenGL Test" into Blender's search menu."""
    
    bl_label = "OpenGL Test"
    bl_idname = 'wm.opengl_test'
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        namespace['projection_matrix'] = bgl.Buffer(bgl.GL_FLOAT, (4, 4))
        
        namespace['points'] = (
            -0.5, -0.5, 0.0,
            0.5, -0.5, 0.0,
            0.0, 0.5, 0.0
        )
        
        namespace['colors'] = (
            0.0, 1.0, 0.0, 0.5,
            1.0, 1.0, 0.0, 0.5,
            1.0, 0.0, 1.0, 0.5
        )
        
        namespace['data_point'] = bgl.Buffer(bgl.GL_FLOAT, len(namespace['points']), namespace['points'])
        namespace['data_color'] = bgl.Buffer(bgl.GL_FLOAT, len(namespace['colors']), namespace['colors'])
        
        namespace['vertex_shader_info'] = bgl.Buffer(bgl.GL_INT, 1)
        namespace['fragment_shader_info'] = bgl.Buffer(bgl.GL_INT, 1)
        namespace['shader_program_info'] = bgl.Buffer(bgl.GL_INT, 1)
        
        namespace['vao'] = bgl.Buffer(bgl.GL_INT, 1)
        namespace['vbo_point'] = bgl.Buffer(bgl.GL_INT, 1)
        namespace['vbo_color'] = bgl.Buffer(bgl.GL_INT, 1)
        
        bgl.glGenBuffers(1, namespace['vbo_point'])
        bgl.glGenBuffers(1, namespace['vbo_color'])
        
        # Shaders
        namespace['shader_program'] = bgl.glCreateProgram()
        
        namespace['vertex_shader'] = bgl.glCreateShader(bgl.GL_VERTEX_SHADER)
        namespace['fragment_shader'] = bgl.glCreateShader(bgl.GL_FRAGMENT_SHADER)
        
        bgl.glShaderSource(namespace['vertex_shader'], vertex_shader_source)
        bgl.glShaderSource(namespace['fragment_shader'], fragment_shader_source)
        
        bgl.glCompileShader(namespace['vertex_shader'])
        bgl.glCompileShader(namespace['fragment_shader'])
        
        bgl.glGetShaderiv(namespace['vertex_shader'], bgl.GL_COMPILE_STATUS, namespace['vertex_shader_info'])
        bgl.glGetShaderiv(namespace['fragment_shader'], bgl.GL_COMPILE_STATUS, namespace['fragment_shader_info'])
        
        if namespace['vertex_shader_info'][0] == bgl.GL_TRUE:
            print("Vertex shader compiled successfully.")
        elif namespace['vertex_shader_info'][0] == bgl.GL_FALSE:
            print("Vertex shader failed to compile.")
        
        if namespace['fragment_shader_info'][0] == bgl.GL_TRUE:
            print("Fragment shader compiled successfully.")
        elif namespace['fragment_shader_info'][0] == bgl.GL_FALSE:
            print("Fragment shader failed to compile.")
        
        bgl.glAttachShader(namespace['shader_program'], namespace['vertex_shader'])
        bgl.glAttachShader(namespace['shader_program'], namespace['fragment_shader'])
        
        bgl.glLinkProgram(namespace['shader_program'])
        
        bgl.glGetProgramiv(namespace['shader_program'], bgl.GL_LINK_STATUS, namespace['shader_program_info'])
        
        if namespace['shader_program_info'][0] == bgl.GL_TRUE:
            print("Shader program linked successfully.")
        elif namespace['shader_program_info'][0] == bgl.GL_FALSE:
            print("Shader program failed to link.")
        
        # glGetUniformLocation can only be used after the shader program is linked, as stated in the OpenGL Specification.
        namespace['perspective_uniform_location'] = bgl.glGetUniformLocation(namespace['shader_program'], "perspective")
        
        bgl.glValidateProgram(namespace['shader_program'])
        
        bgl.glGetProgramiv(namespace['shader_program'], bgl.GL_VALIDATE_STATUS, namespace['shader_program_info'])
        
        if namespace['shader_program_info'][0] == bgl.GL_TRUE:
            print("Shader program validated successfully.")
        elif namespace['shader_program_info'][0] == bgl.GL_FALSE:
            print("Shader program failed to validate.")
        
        draw_handler_add()
        
        namespace['timer'] = context.window_manager.event_timer_add(time_step=0.01, window=context.window)
        namespace['data_timer'] = bgl.Buffer(bgl.GL_FLOAT, 2, [math.sin(namespace['timer'].time_duration), math.sin(namespace['timer'].time_duration) * 2])
        
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if not context.area or not context.region:
            return {'PASS_THROUGH'}
        
        namespace['data_timer'][0] = math.sin(namespace['timer'].time_duration)
        namespace['data_timer'][1] = math.sin(namespace['timer'].time_duration) * 2
        
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, namespace['vbo_point'][0])
        
        # Inserts data from the timer into the Y and Z coordinates of the 3rd vertex, starting at index 7, its Y coordinate.
        index = 7
        float_byte_count = 4
        insertion_size = float_byte_count * 2 # 2 floats are being edited right now: Y position and Z position.
        bgl.glBufferSubData(bgl.GL_ARRAY_BUFFER, index * float_byte_count, insertion_size, namespace['data_timer'])
        
        if event.type == 'ESC' and event.value == 'PRESS':
            context.area.tag_redraw()
            context.window_manager.event_timer_remove(namespace['timer'])
            draw_handler_remove()
            
            return {'FINISHED'}
        
        namespace['projection_matrix'][:] = context.region_data.perspective_matrix
        
        context.area.tag_redraw()
        
        return {'RUNNING_MODAL'}


def draw_handler_add():
    namespace['OPENGL_TEST_HANDLER_2D'] = bpy.types.SpaceView3D.draw_handler_add(draw_pixel, (), 'WINDOW', 'POST_PIXEL')
    namespace['OPENGL_TEST_HANDLER_3D'] = bpy.types.SpaceView3D.draw_handler_add(draw_view, (), 'WINDOW', 'POST_VIEW')


def draw_handler_remove():
    if namespace.get('OPENGL_TEST_HANDLER_2D') is not None:
        bpy.types.SpaceView3D.draw_handler_remove(namespace['OPENGL_TEST_HANDLER_2D'], 'WINDOW')
        namespace['OPENGL_TEST_HANDLER_2D'] = None
    
    if namespace.get('OPENGL_TEST_HANDLER_3D') is not None:
        bpy.types.SpaceView3D.draw_handler_remove(namespace['OPENGL_TEST_HANDLER_3D'], 'WINDOW')
        namespace['OPENGL_TEST_HANDLER_3D'] = None


bpy.utils.register_class(WM_OT_opengl_test)
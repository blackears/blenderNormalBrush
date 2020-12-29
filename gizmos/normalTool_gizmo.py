#Copyright 2019 Mark McKay
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
import math
import mathutils 
from bpy.types import (
    GizmoGroup,
)




class NormalToolWidgetGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_test_camera"
    bl_label = "Object Camera Test Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob and ob.type == 'CAMERA')

    def _create_gizmo(self, obj, axis):
        giz = self.gizmos.new("GIZMO_GT_dial_3d")
        
        props = giz.target_set_operator("transform.rotate")        
        if axis == 0:
            props.constraint_axis = True, False, False
            giz.color = (1, 0, 0)
        elif axis == 1:
            props.constraint_axis = False, True, False
            giz.color = (0, 1, 0)
        else:
            props.constraint_axis = False, False, True
            giz.color = (0, 0, 1)
            
        props.orient_type = 'LOCAL'
        props.release_confirm = True

#        mathutils.Quaternion(obj.matrix_world.x, math.radians(0))

#        giz.matrix_basis = obj.matrix_world.normalized()
        rotMtx = obj.matrix_world.normalized()
        if axis == 0:
            r = mathutils.Matrix.Rotation(math.radians(90), 4, (1, 0, 0))
            rotMtx = rotMtx @ r
#            rotMtx = ob.matrix_world.normalized().rotate(mathutils.Euler((math.radians(90), 0, 0), 'XYZ'))
        elif axis == 1:
            r = mathutils.Matrix.Rotation(math.radians(90), 4, (0, 1, 0))
            rotMtx = rotMtx @ r
#            rotMtx = ob.matrix_world.normalized().rotate(mathutils.Euler((0, math.radians(90), 0), 'XYZ'))
        else:
            r = mathutils.Matrix.Rotation(math.radians(90), 4, (0, 0, 1))
            rotMtx = rotMtx @ r
#            rotMtx = ob.matrix_world.normalized().rotate(mathutils.Euler((0, 0, math.radians(90)), 'XYZ'))
            pass
            
        giz.matrix_basis = rotMtx
       
        
        giz.line_width = 3

#        mpr.color = 0.8, 0.8, 0.8
        giz.alpha = 0.5

        giz.color_highlight = 1.0, 1.0, 1.0
        giz.alpha_highlight = 1.0
        
        return giz


    def setup(self, context):
        # Run an operator using the dial gizmo
        obj = context.object
#        mpr = self.gizmos.new("GIZMO_GT_dial_3d")
        self.gizRotX = self._create_gizmo(obj, 0)
        self.gizRotY = self._create_gizmo(obj, 1)
        self.gizRotZ = self._create_gizmo(obj, 2)

#        gizRotX = self.gizmos.new("GIZMO_GT_dial_3d")
#        props = gizRotX.target_set_operator("transform.rotate")
#        props.constraint_axis = True, False, False
#        props.orient_type = 'LOCAL'
#        props.release_confirm = True

#        gizRotX.matrix_basis = obj.matrix_world.normalized()
#        gizRotX.line_width = 3

#        mpr.color = 0.8, 0.8, 0.8
#        gizRotX.alpha = 0.5

#        gizRotX.color_highlight = 1.0, 1.0, 1.0
#        gizRotX.alpha_highlight = 1.0

#        self.gizRotX = gizRotX
        
        
        
        

    def refresh(self, context):
        ob = context.object
        rotMtx = ob.matrix_world.normalized()
        
        grX = self.gizRotX
#        grX.matrix_basis = ob.matrix_world.normalized()
#        grX.matrix_basis = ob.matrix_world.normalized().rotate(mathutils.Euler((math.radians(90), 0, 0), 'XYZ'))
        r = mathutils.Matrix.Rotation(math.radians(90), 4, (1, 0, 0))
        grX.matrix_basis = rotMtx @ r
    
#        r = mathutils.Matrix.Rotation(math.radians(90), 4, (1, 0, 0))
#        rotMtx = rotMtx.m @ r
        grY = self.gizRotY
#        grY.matrix_basis = ob.matrix_world.normalized().rotate(mathutils.Euler((0, math.radians(90), 0), 'XYZ'))
        r = mathutils.Matrix.Rotation(math.radians(90), 4, (0, 1, 0))
        grY.matrix_basis = rotMtx @ r
        
        grZ = self.gizRotZ
#        grZ.matrix_basis = ob.matrix_world.normalized().rotate(mathutils.Euler((0, 0, math.radians(90)), 'XYZ'))
#        grZ.matrix_basis = ob.matrix_world.normalized()
        r = mathutils.Matrix.Rotation(math.radians(90), 4, (0, 0, 1))
        grZ.matrix_basis = rotMtx @ r



def register():
    print ("--Registering NormalToolWidgetGroup")
    bpy.utils.register_class(NormalToolWidgetGroup)
    #bpy.utils.register_class(AddStairs)
    #bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    print ("--Unregistering NormalToolWidgetGroup")
    bpy.utils.unregister_class(NormalToolWidgetGroup)
    #bpy.utils.unregister_class(AddStairs)
    #bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()

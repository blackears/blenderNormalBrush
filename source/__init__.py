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


bl_info = {
    "name": "Normals Brush",
    "description": "Provides a brush that lets you adjust normals.  Also a button for copying normals that lie along seams.",
    "author": "Mark McKay",
    "version": (1, 2, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
#    "wiki_url": "https://github.com/blackears/normalTool",
    "tracker_url": "https://github.com/blackears/normalTool",
    "category": "View 3D"
}

import bpy
import importlib


if "bpy" in locals():
    if "normalTool" in locals():
        importlib.reload(normalTool)
    else:
        from .ops import normalTool
        
    if "fixSeamNormals" in locals():
        importlib.reload(fixSeamNormals)
    else:
        from .ops import fixSeamNormals
        
else:
    from .ops import normalTool
    from .ops import fixSeamNormals

def register():
    normalTool.register()
    fixSeamNormals.register()


def unregister():
    normalTool.unregister()
    fixSeamNormals.unregister()


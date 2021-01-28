# Copyright 2019 Mark McKay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


bl_info = {
    "name": "Normal Tool",
    "description": "Provides a brush that lets you interactively adjust normals.  Also provides some useful operators.",
    "author": "Mark McKay",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "wiki_url": "https://github.com/blackears/normalTool",
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
else:
    from .ops import normalTool

def register():
    normalTool.register()


def unregister():
    normalTool.unregister()


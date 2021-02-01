# Normal Brush for Blender

Adds a new control to Blender that allows you to adjust normals by stroking with your pen or mouse.

Once you install the tool, a new panel will be added to the 'N' menu on the right side of your viewport under the Kitfox tab.  

### Normal Brush Tool

[The Normal Brush Tool in action](doc/normalBrushInAction.png)

The **Normal Brush** submenu contains controls for the brush.  To begin, select the object you want to adjust normals on and then click the **Start Normal Tool** button to activate the brush.  The normals of the object will then be shown overlaid on the mesh and you can click and drag with the brush to adjust them.

##### Strength
Adjust the strength of the brush stroke.

##### Normal Length
Change the display size normals are drawn in the overlay.

##### Radius
Raidus of the normal brush.  You can also press the *[* and *]* keys to change the size.

##### Front Faces Only
If checked, your brush stroke will only affect faces facing the viewer.  Otherwise, all vertices within a sphere the size of the brush are affected.

##### Mode Buttons
- **Fixed** - Brush stroke will paint all normals to point in a single direction.
- **Attract** - Normals will point toward origin of selected target object.
- **Repel** - Normals will point away from origin of selected target object.
- **Vertex** - Paint normals to reflect the underlying geometry.  This effectively 'erases' your tweaks.

##### Normal
In **Fixed** mode, indictates the directon of the normal you are painting.  You can set it directly by typing in the normal or select *Exact Normal* to get a trackball you can use to adjust the normal.  You can also click the *Pick Normal* button to get an eyedrpper to pick the normal from another piece of geometry in the scene.

##### Target
In **Attract** and **Repel** modes, indicates the target objects that normals will point toward/away from.

### Fix Seam Normals Tool

Also included under the **Fix Seam Normals** menu is a control to automatically copy normals across seams.  Simply select two or more objects with edges that meet.  Then press the **Copy Seam Normals** button.  The normals from the active object will be copied to the other selected objects wherever the selected object' vertex is snapped to the same spot as the active object's vertex.

## Installation

To install, download this archive as a .zip file.  Then start blender and open your Edit > Preferences.  Select the Add-ons tab and then press the Install button.  Browse to the .zip file and select it.  Finally, tick the checkbox next to Add Mesh: Normal Brush.

## Further Information

This stairs plugin is also being distributed on the Blender market:
https://blendermarket.com/products/blender-stairs

A video giving a quick tour of the plugin is available here:

[![Video thumbnail](https://img.youtube.com/vi/YlNnEIQWd2k/0.jpg)](https://www.youtube.com/watch?v=YlNnEIQWd2k)
[![Video thumbnail](https://img.youtube.com/vi/YbwRDwlplXo/0.jpg)](https://www.youtube.com/watch?v=YbwRDwlplXo)

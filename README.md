# Normal Brush for Blender

Adds a new control to Blender that allows you to adjust normals by stroking your model with a brush.

Once you install the tool, a new panel will be added to the 'N' menu on the right side of your viewport under the Kitfox tab.  

### Normal Brush Tool

![The Normal Brush Tool in action](doc/normalBrushInAction.png)

The **Normal Brush** submenu contains controls for the brush.  To begin, select the object you want to adjust normals on and then click the **Start Normal Tool** button to activate the brush.  The normals of the object will then be shown overlaid on the mesh and you can click and drag with the brush to adjust them.

##### Strength
Adjust the strength of the brush stroke.

##### Pen Pressure
If checked, the strength of the brush stroke is multiplied by the pressure of your pen.

##### Normal Length
Change the display size normals are drawn in the overlay.

##### Radius
Radius of the normal brush.  You can also press the *[* and *]* keys to change the size.

##### Front Faces Only
If checked, your brush stroke will only affect faces facing the viewer.  Otherwise, all vertices within a sphere the size of the brush are affected.

##### Selected Faces Only
If checked, your brush stroke will only affect faces that have been selected in edit mode.  (The Normal Brush tool still operates in Object mode).

##### Symmetry
For each axis checked, any tweak made on one part of the model will also be mirrored across the axis.

##### Mode Buttons
- **Comb** - Normals will point in the direction that you stroke the brush.
- **Fixed** - Brush stroke will paint all normals to point in a single direction.
- **Attract** - Normals will point toward origin of selected target object.
- **Repel** - Normals will point away from origin of selected target object.
- **Smooth** - Average the values of the normals under the brush.
- **Vertex** - Paint normals to reflect the underlying geometry.  This effectively 'erases' your tweaks.

##### Normal
In **Fixed** mode, indicates the direction of the normal you are painting.  You can set it directly by typing in the normal or select *Exact Normal* to get a trackball you can use to adjust the normal.  You can also click the *Pick Normal* button to get an eyedropper to pick the normal from another piece of geometry in the scene.

##### Target
In **Attract** and **Repel** modes, indicates the target objects that normals will point toward/away from.

##### Undo/Redo
While the tool is running, you can use **CTRL-Z** to undo your most recent brush stroke and **CTRL-SHIFT-Z** to redo it.  The history is limited to 10 strokes.  Once you press **Enter** to finish editing normals, all your changes are added to Blender's undo queue as a group and you can no longer undo individual strokes.

##### Cancelling
Pressing **Esc** or **Right Mouse Click** will cancel your editing, discarding all changes.

### Seam Normal Tools

These tools adjust the normals on the boundaries of objects.

#### Smooth Seam Normals

Use this after you Separate a smooth mesh into two pieces and want to make the edge normals match up like they're still connected while still keeping them as separate objects.

Select two or more objects with edges that meet.  Then press the **Smooth Seam Normals** button.  The normals on the boundary edge of the selected objects will be averaged with the geometry of all other selected objects and the split normals updated to create a seamless surface.


#### Copy Seam Normals

There is another button for **Copy Seam Normals**.  The will copy the normals of the vertices on the edge boundary of the active object to all other selected objects.

## Building

To build, execute the *makeDeploy.py* script in the root of the project.  It will create a directory called *deploy* that contains a zip file containing the addon.

## Installation

To install, start Blender and select Edit > Preferences from the menubar.  Select the Add-ons tab and then press the Install button.  Browse to the .zip file that you built and select it.  Finally, tick the checkbox next to Add Mesh: Normal Brush.

## Further Information

This addon is available from the Blender market:

https://blendermarket.com/products/normal-brush

A video giving a quick tour of the plugin is available here:

[![Video thumbnail](https://img.youtube.com/vi/c9lulhKmsvE/0.jpg)](https://www.youtube.com/watch?v=c9lulhKmsvE)

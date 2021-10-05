bl_info = {
    "name" : "MobibamStudio",
    "author" : "Samy",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

import bpy
import os
import time
from bpy.types import (Panel, Operator,PropertyGroup)
from bpy.props import (StringProperty, FloatProperty, BoolProperty,PointerProperty)
from bpy_extras.io_utils import ImportHelper

class MyProperties(PropertyGroup):
    
    filter_glob: StringProperty(
        default='*.obj',
        options={'HIDDEN'}
    )
        
    closet_width: FloatProperty(
        name = "Largeur du meuble",
        description="Largeur du meuble, en mètre",
        default = 1.2,
        min = 0.2,
        max = 4.0
    )
    
    is_high : BoolProperty(
        name="Meuble haut",
        description="A cocher si le meuble est un meuble haut, permet d'élever le meuble à 1.4m",
        default = False
    )
            
    
class MOB_STUDIO_OT_Import(Operator, ImportHelper):
    bl_idname = "mobibam.import"
    bl_label = "Import closet"
    bl_description = "Import un meuble et le place au bon endroit dans la scène"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
    
        # Import model
        bpy.ops.import_scene.obj(filepath=self.filepath)
        
        # Get closet id
        filename, extension = os.path.splitext(self.filepath)
        closet_id = os.path.split(filename)[-1]
        
        # Check if collection exist
        coll = bpy.data.collections.get(closet_id)
        print(coll)
        if coll is not None:
            print('Closet already exist')
            bpy.ops.object.delete(use_global=False, confirm=False)
            return {'FINISHED'}
        
        else:
            # Create new collection and move items to it
            bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name=closet_id)
            
            # 
            bpy.ops.object.select_all(action='DESELECT')
            
            for obj in bpy.data.collections[closet_id].all_objects:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
            
            bpy.ops.object.join()
            
            # Rename mesh to closet_id
            bpy.context.selected_objects[0].name=closet_id
            
            #Get scale factor bases on closet width
            meshDimension = bpy.context.object.dimensions.x
            meshScale = bpy.context.object.scale.x
            factor = (meshScale * mytool.closet_width) / meshDimension
            bpy.context.object.scale=(factor, factor, factor)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            ## Get ground infos
            # Check wall offset
            distToCenter = bpy.data.objects['mur'].location.y
            distToWall = bpy.data.objects['mur'].dimensions.y / 2 - (abs(distToCenter))
            print('distToCenter : ', distToCenter)
            
            # Move mesh to ground
            closetHeight = bpy.context.object.dimensions.z
            closetDepth = bpy.context.object.dimensions.y
            
            
            bpy.context.object.location[2] = closetHeight / 2
            
            print('toWall :',distToWall - closetDepth)
            
            # Move origin point to bottom of mesh
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            
            # Move closet to wall 
            bpy.context.object.location[1] = distToWall - closetDepth / 2
            
            # If high_closet, move it to 1.4m
            if (mytool.is_high == True):
                bpy.context.object.location[2] = 1.4
            
            return {'FINISHED'}


class MOB_STUDIO_OT_Render(Operator):
    bl_idname = "mobibam.render"
    bl_label = "Rener closet"
    bl_description = "Render tous les meubles dans la collection 'Renders'"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        print("Automated Export Script Started")
        closet_list = bpy.data.collections['Renders'].children
        total_closet = len(closet_list)
        print ("Total of closets : ", total_closet)
        filename = bpy.path.basename(bpy.context.blend_data.filepath).split('.')[0]
        
        filepath = bpy.data.filepath
        dest = os.path.dirname(filepath) + '/renders'

        # hide everything
        for collection in closet_list:
            collection.hide_render = True

        progress = 0
        
        for collection in closet_list:
            collection.hide_render = False
            bpy.data.scenes[0].render.filepath = os.path.join(dest, filename + '_' + collection.name + '.png')
            print("Rendering item ", progress + 1) 
            bpy.ops.render.render(write_still=True)
            collection.hide_render = True
            progress = progress + 1
            print(progress, " / ", total_closet)
        
        print("Sript End")
        return {'FINISHED'}
    
    
class MOB_STUDIO_PT_Import_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Import de meuble"
    bl_category = "Mobibam Studio"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        
        
        header_row = layout.row()
        header_row.scale_y = 2
        header_row.label(text='Mobibam Studio')
        

        layout.prop(mytool, "closet_width")
        layout.prop(mytool, "is_high", text="Meuble haut")
        
        row = layout.row()
        row.scale_y = 2
        row.operator(MOB_STUDIO_OT_Import.bl_idname, text="Import closet")
        
        
class MOB_STUDIO_PT_Render_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Export de meuble"
    bl_category = "Mobibam Studio"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        
        row = layout.row()
        row.scale_y = 2
        row.operator(MOB_STUDIO_OT_Render.bl_idname, text="Render multiple")
               
        

def register():
    bpy.utils.register_class(MOB_STUDIO_OT_Import)
    bpy.utils.register_class(MOB_STUDIO_OT_Render)
    bpy.utils.register_class(MOB_STUDIO_PT_Import_Panel)
    bpy.utils.register_class(MOB_STUDIO_PT_Render_Panel)
    bpy.utils.register_class(MyProperties)
    
    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    bpy.utils.unregister_class(MOB_STUDIO_OT_Import)
    bpy.utils.unregister_class(MOB_STUDIO_OT_Render)
    bpy.utils.unregister_class(MOB_STUDIO_PT_Import_Panel)
    bpy.utils.unregister_class(MOB_STUDIO_PT_Render_Panel)
    bpy.utils.unregister_class(MyProperties)
    
    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()
    
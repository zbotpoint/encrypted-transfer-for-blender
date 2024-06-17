import bpy

# operator class for our encrypted transfer dialogue
class SCENE_OT_encrypted_transfer(bpy.types.Operator):
    
    # define some basic properties of our operator
    bl_idname = "object.encrypted_trasnfer"
    bl_label = "Encrypted Transfer"
    bl_description = "Securely transfer a file to a remote location"
    bl_options = {"REGISTER"}
    
    # invoke runs when the operator is called from the menu
    def invoke(self, context, event):
        # display a dialogue box to the user
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    # describe how to draw the dialogue box
    def draw(self, context):
        pass
    
    # execute runs upon completion of the dialogue
    def execute(self, context):
        return {'FINISHED'}

def register():
    bpy.utils.register_class(SCENE_OT_encrypted_transfer)
    
def unregister():
    bpy.utils.unregister_class(SCENE_OT_encrypted_transfer)

if __name__ == "__main__":
    register()
import bpy
from encrypted_transfer_utils import *

bl_info = {
    "name": "Encrypted Transfer for Blender",
    "author": "zbotpoint",
    "version": (1, 0),
    "blender": (2, 65, 0),
    "description": "Transfer Blender files securely to a remote location",
    "category": "Import-Export",
}


# operator class for our encrypted transfer dialogue
class WM_OT_encrypted_transfer(bpy.types.Operator):

    # define some basic properties of our operator
    bl_idname = "wm.encrypted_transfer"
    bl_label = "Encrypted Transfer"
    bl_description = "Securely transfer a file to a remote location"
    bl_options = {"REGISTER"}

    # invoke runs when the operator is called from the menu
    def invoke(self, context, event):
        # display a dialogue box to the user
        return context.window_manager.invoke_props_dialog(self, width=400)

    # describe how to draw the dialogue box
    def draw(self, context):
        layout = self.layout
        pass

    # execute runs upon completion of the dialogue
    def execute(self, context):
        sym_key, nonce = generate_sym_key_nonce()
        print(nonce)
        return {"FINISHED"}


# function to extend the menu with our add-on
def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(WM_OT_encrypted_transfer.bl_idname, text="Encrypted Transfer")


# functions that are called when this blender add-on is loaded and unloaded
def register():
    bpy.utils.register_class(WM_OT_encrypted_transfer)

    # insert our add-on menu item into the file menu
    bpy.types.TOPBAR_MT_file.append(menu_func)


def unregister():
    bpy.utils.unregister_class(WM_OT_encrypted_transfer)

    # remove our add-on from the menu
    bpy.types.TOPBAR_MT_file.remove(menu_func)


if __name__ == "__main__":
    register()

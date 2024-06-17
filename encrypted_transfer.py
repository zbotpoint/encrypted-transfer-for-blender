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

# Define the list of remote key providers
key_provider_list = [
    ("key_provider_gitlab", "GitLab", "Use GitLab as the remote key provider"),
    ("key_provider_github", "GitHub", "Use GitHub as the remote key provider"),
]


# operator class for our encrypted transfer dialogue
class WM_OT_encrypted_transfer(bpy.types.Operator):

    # define some basic properties of our operator
    bl_idname = "wm.encrypted_transfer"
    bl_label = "Encrypted Transfer"
    bl_description = "Securely transfer a file to a remote location"
    bl_options = {"REGISTER"}

    # dropdown list for selecting the key provider
    key_provider: bpy.props.EnumProperty(
        name="Key Provider",
        description="Choose a remote key provider",
        items=key_provider_list,
        default="key_provider_github",
    )

    # textbox for the user to enter the name of the recipient
    recipient_username: bpy.props.StringProperty(
        name="Recipient Username",
        description="Enter the username of the intended recipient",
    )

    # define a path input for the user to locate their signing keys
    local_key_path: bpy.props.StringProperty(
        name="Local Keys", description="Select which keys to use", subtype="DIR_PATH"
    )

    # invoke runs when the operator is called from the menu
    def invoke(self, context, event):
        # display a dialogue box to the user
        return context.window_manager.invoke_props_dialog(self)

    # describe how to draw the dialogue box
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "local_key_path")
        layout.prop(self, "key_provider")
        layout.prop(self, "recipient_username")

    # execute runs upon completion of the dialogue
    def execute(self, context):
        key_provider = self.key_provider
        local_key_path = self.local_key_path
        username = self.recipient_username
        self.report(
            {"INFO"},
            f"Selected provider: {key_provider}, Key path: {local_key_path}, Username: {username}",
        )

        if key_provider == "key_provider_github":
            key_provider = "github"
        elif key_provider == "key_provider_gitlab":
            key_provider == "gitlab"

        # store all of the relevant asymmetrical (public/private) keys
        remote_pubkey = fetch_remote_public_key(key_provider, username)
        local_pubkey = cryptography.hazmat.primitives.serialization.load_ssh_public_key(
            read_file(local_key_path + "id_rsa.pub")
        )
        local_privkey = (
            cryptography.hazmat.primitives.serialization.load_ssh_private_key(
                read_file(local_key_path + "id_rsa"), None
            )
        )

        # generate a symmetric key and a nonce to be used for this message
        symmetric_key, nonce = generate_sym_key_nonce()

        # save our .blend file to a temp location and load it
        save_path = r"C:\Users\zacha\Desktop\scene.blend.tmp"
        bpy.ops.wm.save_mainfile(filepath=save_path)
        blender_data = read_file(save_path)

        # try encrypting the file and writing it to a temp location
        try:
            cipher_data = sym_encrypt_data(symmetric_key, nonce, blender_data)
            save_path = r"C:\Users\zacha\Desktop\scene.blend.cipher.tmp"
            write_file(cipher_data, save_path)
        except OverflowError:
            self.report(
                {"ERROR"},
                "This file is too large to encrypt. Files must be less than 2GB in size.",
            )

        ###### After this line, we pretend we are the recipient for testing purposes

        # receive the key and nonce from the blender user

        # try to decrypt the file
        try:
            cipher_data = read_file(r"C:\Users\zacha\Desktop\scene.blend.cipher.tmp")
            unencrypted_data = sym_decrypt_data(symmetric_key, nonce, cipher_data)
        except cryptography.exceptions.InvalidTag:
            self.report(
                {"ERROR"},
                "Authentication tag for this file failed to validate. The data has been modified or decryption failed.",
            )

        # write the decrypted data to a .blend file
        save_path = r"C:\Users\zacha\Desktop\scene.clear.blend"
        write_file(unencrypted_data, save_path)

        # try to open the decrypted file
        # this should open and be identical to how the file was before running the add-on
        bpy.ops.wm.open_mainfile(filepath=save_path)

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

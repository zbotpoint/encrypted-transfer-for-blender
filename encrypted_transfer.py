import bpy
import socket
import json
import base64

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

    # destination fields
    dest_ip: bpy.props.StringProperty(
        name="Destination",
        description="Enter the name of the remote host of the recipient",
    )
    dest_port: bpy.props.StringProperty(
        name="port",
        description="Enter the port on the remote host",
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
        layout.prop(self, "dest_ip")
        layout.prop(self, "dest_port")

    # execute runs upon completion of the dialogue
    def execute(self, context):
        key_provider = self.key_provider
        local_key_path = self.local_key_path
        username = self.recipient_username
        dest_ip = self.dest_ip
        dest_port = int(self.dest_port)
        self.report(
            {"INFO"},
            f"Selected provider: {key_provider}, Key path: {local_key_path}, Username: {username}",
        )
        self.report({"INFO"}, f"Destination: {dest_ip}:{dest_port}")

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
        save_path = r"C:\Users\zacha\AppData\Local\Temp\scene.blend.tmp"
        bpy.ops.wm.save_mainfile(filepath=save_path)
        blender_data = read_file(save_path)

        # generate a signature of the file using our local private key
        # so our recipient can verify our identity when they receive it
        signature = sign_data(local_privkey, blender_data)

        # put all of the sensitive info into a struct so we can encrypt it together
        data_to_be_sym_encrypted = json.dumps(
            {
                "recipient": username,
                "blender_data": base64.b64encode(blender_data).decode("utf-8"),
                "signature": base64.b64encode(signature).decode("utf-8"),
            }
        ).encode("utf-8")

        # put our symmetric key and nonce asymmetrically with the recipient's public key
        # they will decrypt with their private key
        data_to_be_asym_encrypted = json.dumps(
            {
                "symmetric_key": base64.b64encode(symmetric_key).decode("utf-8"),
                "nonce": base64.b64encode(nonce).decode("utf-8"),
            }
        ).encode("utf-8")

        # try encrypting the data
        try:
            sym_encrypted_data = sym_encrypt_data(
                symmetric_key, nonce, data_to_be_sym_encrypted
            )
        except OverflowError:
            self.report(
                {"ERROR"},
                "This file is too large to encrypt. Files must be less than 2GB in size.",
            )

        asym_encrypted_data = asym_encrypt_data(
            remote_pubkey, data_to_be_asym_encrypted
        )

        # create a json object for sending our data
        packet = {
            "asym_encrypted_data": base64.b64encode(asym_encrypted_data).decode(
                "utf-8"
            ),
            "sym_encrypted_data": base64.b64encode(sym_encrypted_data).decode("utf-8"),
        }
        data = json.dumps(packet).encode("utf-8")

        # try sending encrypted data to a listener
        # in this POC, this is just another program on this machine
        host = dest_ip
        port = dest_port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            s.connect((host, port))
            s.sendall(data)
            s.close()
            self.report(
                {"INFO"},
                f"Sent {len(data)} bytes to {host}:{port} successfully.",
            )
        except socket.error:
            self.report(
                {"ERROR"},
                f"Failed to connect to remote at {host}:{port}.",
            )

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

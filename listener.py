import socket
import json
import base64
from subprocess import call
from encrypted_transfer_utils import *

host = ""
port = 4567
data = b""


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((host, port))

    print(f"Start listening on {host}:{port}")
    s.listen(1)
    conn, addr = s.accept()
    with conn:
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                break
            data += chunk

packet = json.loads(data)
print("Received all data")

# sender_public_key_path = r"C:\Users\zacha\Desktop\keys\id_rsa.pub"
sender_pubkey = cryptography.hazmat.primitives.serialization.load_ssh_public_key(
    read_file(sender_public_key_path)
)
sender_pubkey = fetch_remote_public_key(key_provider, username)

local_privkey = cryptography.hazmat.primitives.serialization.load_ssh_private_key(
    read_file(r"C:\Users\zacha\.ssh\id_rsa"), None
)

asym_encrypted_data = base64.b64decode(packet["asym_encrypted_data"])
sym_encrypted_data = base64.b64decode(packet["sym_encrypted_data"])

unencrypted_data = asym_decrypt_data(local_privkey, asym_encrypted_data)
unencrypted_data = json.loads(unencrypted_data)
symmetric_key = base64.b64decode(unencrypted_data["symmetric_key"])
nonce = base64.b64decode(unencrypted_data["nonce"])
print("Successfully decrypted one-time symmetric key and nonce.")

try:
    unencrypted_data = sym_decrypt_data(symmetric_key, nonce, sym_encrypted_data)
    print("Successfully decrypted data.")

    unencrypted_data = json.loads(unencrypted_data)
    blender_data = base64.b64decode(unencrypted_data["blender_data"])
    recipient = unencrypted_data["recipient"]
    signature = base64.b64decode(unencrypted_data["signature"])

    print(f"Recipient is {recipient}")

    if verify_data(sender_pubkey, blender_data, signature):
        print("Signature authenticated.")

        # write the decrypted data to a .blend file
        save_path = r"C:\Users\zacha\Documents\Projects\encrypted-transfer-for-blender\scene.unencrypted.blend"
        write_file(blender_data, save_path)
        print("Saved to file.")

        blender_exe_path = (
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe"
        )
        # call([blender_exe_path, save_path])

    else:
        print("Signature could not authenticate.")

except cryptography.exceptions.InvalidTag:
    print(
        "Authentication tag for this file failed to validate. The data has been modified or decryption failed."
    )

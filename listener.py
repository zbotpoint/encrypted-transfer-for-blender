import socket
import json
import base64
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
                print("broke")
                break
            print("Received 1024 bytes")
            data += chunk

packet = json.loads(data)
print("Received all data")

symmetric_key = base64.b64decode(packet["symmetric_key"])
nonce = base64.b64decode(packet["nonce"])
encrypted_data = base64.b64decode(packet["encrypted_data"])
try:
    unencrypted_data = sym_decrypt_data(symmetric_key, nonce, encrypted_data)
    print("Successfully decrypted data.")

    # write the decrypted data to a .blend file
    save_path = r"C:\Users\zacha\Desktop\scene.unencrypted.blend"
    write_file(unencrypted_data, save_path)

except cryptography.exceptions.InvalidTag:
    print(
        "Authentication tag for this file failed to validate. The data has been modified or decryption failed."
    )

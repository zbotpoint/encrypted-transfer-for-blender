import bpy
import os
import subprocess
import requests
import sys

try:
    sys.path.append(r"c:\users\zacha\appdata\roaming\python\python311\site-packages")
    import cryptography
except ImportError:
    py_exec = str(sys.executable)
    lib = Path(py_exec).parent.parent / "lib"
    subprocess.call([py_exec, "-m", "ensurepip", "--user"])
    subprocess.call([py_exec, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.call([py_exec, "-m", "pip", "install", "--user", "encryption"])

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import padding


# fetches another user's remote public key from a provider
def fetch_remote_public_key(provider, username):
    url = f"https://api.{provider}.com/users/{username}/keys"
    response = requests.get(url)

    if response.status_code == 200:
        keys = response.json()
        key = keys[0]["key"]
        key = key.encode()
        return serialization.load_ssh_public_key(key)
    else:
        print(f"Failed to fetch keys for {username}: {response.status_code}")
        return None


# helper functions for reading/writing files
def read_file(file_path):
    file_path = os.path.normpath(file_path)
    with open(file_path, "rb") as f:
        data = f.read()
    return data


def write_file(data, file_path):
    file_path = os.path.normpath(file_path)
    with open(file_path, "wb") as f:
        f.write(data)


# generates a symmetric key and nonce that will be used for ChaCha20Poly1305
def generate_sym_key_nonce():
    key = ChaCha20Poly1305.generate_key()
    nonce = os.urandom(12)

    return key, nonce


# encrypts data using a symmetric key
def sym_encrypt_data(sym_key, nonce, data, associated_data=b""):
    chacha = ChaCha20Poly1305(sym_key)

    cipher_data = chacha.encrypt(nonce, data, associated_data)
    return cipher_data


# decrypts data that was encrypted symetrically
def sym_decrypt_data(sym_key, nonce, cipher_data, associated_data=b""):
    chacha = ChaCha20Poly1305(sym_key)

    decrypted_data = chacha.decrypt(nonce, cipher_data, associated_data)
    return decrypted_data


# encrypts data asymetrically, i.e. using the recipient's public key
def asym_encrypt_data(asym_public_key, data):
    # encrypt the data using the foreign pubkey
    # padding is necessary to ensure hardening against some attacks
    encrypted_data = asym_public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return encrypted_data


# decrypts data asymetrically, i.e. using a private key
def asym_decrypt_data(asym_private_key, data):
    decrypted_data = asym_private_key.decrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return decrypted_data

from Crypto.Cipher import AES
import os

import helpers
import m3u8
from pkcs7 import PKCS7Encoder

class IV:
    def __init__(self, iv, key_name):
        self.iv = iv
        self.uri = key_name.replace(".bin", ".iv")

    def __str__(self):
        return '0X' + self.iv.encode('hex')

def save_new_key(new_key, destination_path):
    key_filename = os.path.join(destination_path, os.path.basename(new_key.uri))
    iv_filename = os.path.join(destination_path, os.path.basename(new_key.iv.uri))

    if not os.path.exists(key_filename):
        with open(key_filename, 'wb') as f:
            f.write(new_key.key_value)

        with open(iv_filename, 'wb') as f:
            f.write(new_key.iv.iv)

    else:
        # change modification time so the file is not removed by hlsclient.cleaner.clean
        os.utime(key_filename, None)
        os.utime(iv_filename, None)

def get_key_name(m3u8_uri):
    return os.path.basename(m3u8_uri).replace('.m3u8', '.bin')

def create_key(key_name):
    iv = IV(os.urandom(16), key_name)
    key = m3u8.model.Key(method='AES-128', uri=key_name, baseuri=None, iv=iv)
    key.key_value = os.urandom(16)
    return key

def get_key_from_disk(key_name, full_path):
    key_path = os.path.join(full_path, key_name)
    if not os.path.exists(key_path):
        return False

    with open(key_path, "r") as f:
        key_value = f.read()

    iv_path = key_path.replace('.bin', '.iv')
    with open(iv_path, "r") as f:
        iv_value = f.read()

    iv = IV(iv_value, key_name)
    key = m3u8.model.Key(method='AES-128', uri=key_name, baseuri=None, iv=iv)
    key.key_value = key_value
    return key

def get_key_iv(key):
    iv = str(key.iv)[2:] # Removes 0X prefix
    return iv.decode('hex')

def get_key(key_name, full_path):
    key = get_key_from_disk(key_name, full_path)
    if not key:
        key = create_key(key_name)
    return key

def encrypt(data, key):
    encoder = PKCS7Encoder()
    padded_text = encoder.encode(data)
    encryptor = AES.new(key.key_value, AES.MODE_CBC, get_key_iv(key))
    encrypted_data = encryptor.encrypt(padded_text)

    return encrypted_data

def decrypt(data, key):
    encoder = PKCS7Encoder()
    decryptor = AES.new(key.key_value, AES.MODE_CBC, get_key_iv(key))
    plain = decryptor.decrypt(data)

    return encoder.decode(plain)

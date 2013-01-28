from Crypto.Cipher import AES
import math
import os
import StringIO

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

def adjust_size(x, base=16):
    y = int(base * math.floor(float(x)/base))
    return base if y == 0 else y

class Encrypt(object, StringIO.StringIO):
    '''
    A helper class which can be used for encrypting data in chunks

    Parameters:

     `dataf`
       A file object which contains the content to be encrypted

     `key`
       The key object to be used for encryption
    '''
    def __init__(self, dataf, key):
        self.encryptor = AES.new(key.key_value, AES.MODE_CBC, get_key_iv(key))
        self.dataf = dataf
        self.size = 0
        self.padded = False
        self.pblock = None
        super(Encrypt, self).__init__()

    def get_padding(self):
        '''
        Returns the padding that has to be added to the data. If the padding
        is already added, it responds with an empty string
        '''
        if self.padded:
            return ''

        self.padded = True
        encoder = PKCS7Encoder()
        padding = encoder.get_padding(self.size)
        self.size += len(padding)
        return padding

    def read(self, size):
        '''
        Reads a maximum of 'size' bytes from the input file, encrypts it
        and returns it. This function takes care of ensuring that the 16byte
        boundary is maintained for encryption
        '''

        # Adjust the size to a 16 byte boundary
        size = adjust_size(size)

        # Make a record of the first chunk. Required for adding a padding
        # at the end of the file
        if self.pblock is None:
            self.pblock = self.dataf.read(size)
            self.size += len(self.pblock)

        # Read another chunk and check if end of file has reached
        data = self.dataf.read(size)
        self.size += len(data)

        if not data:
            # Time to add padding
            data = self.pblock + self.get_padding()
            self.pblock = ''
        else:
            # Send the previous chunk back to the user and keep this
            # chunk for next cycle
            pdata = self.pblock
            self.pblock = data
            data = pdata

        if data:
            data = self.encryptor.encrypt(data)

        return data

class Decrypt(object, StringIO.StringIO):
    '''
    A helper class which can be used for decrypting data in chunks

    Parameters:

     `dataf`
       A file object which contains the content to be decrypted

     `key`
       The key object to be used for decryption
    '''
    def __init__(self, dataf, key):
        self.decryptor = AES.new(key.key_value, AES.MODE_CBC, get_key_iv(key))
        self.dataf = dataf
        self.pblock = None
        super(Decrypt, self).__init__()

    def read(self, size):
        '''
        Reads a maximum of 'size' bytes from the input file, decrypts it
        and returns it. This function takes care of ensuring that the 16byte
        boundary is maintained for decryption
        '''

        size = adjust_size(size)

        # Make a record of the first chunk
        if self.pblock is None:
            self.pblock = self.dataf.read(size)
        elif not self.pblock:
            return self.pblock

        # Read the next chunk
        plain = self.decryptor.decrypt(self.pblock)
        self.pblock = self.dataf.read(size)

        if not self.pblock:
            encoder = PKCS7Encoder()
            plain = encoder.decode(plain)

        return plain

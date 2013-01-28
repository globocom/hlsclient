#Taken from http://programmerin.blogspot.com.br/2011/08/python-padding-with-pkcs7.html
from binascii import hexlify, unhexlify

class InvalidBlockSizeError(Exception):
    """Raised for invalid block sizes"""

class PKCS7Encoder():
    """
    Technique for padding a string as defined in RFC 2315, section 10.3,
    note #2
    """

    def __init__(self, block_size=16):
        if block_size < 1 or block_size > 99:
            raise InvalidBlockSizeError('The block size must be between 1 ' \
                    'and 99')
        self.block_size = block_size

    def get_padding(self, text_length):
        amount_to_pad = self.block_size - (text_length % self.block_size)
        pad = unhexlify('%02d' % amount_to_pad)
        return pad * amount_to_pad

    def encode(self, text):
        return text + self.get_padding(len(text))

    def decode(self, text):
        pad = int(hexlify(text[-1]))
        return text[:-pad]

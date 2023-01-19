import base64
from Crypto.Cipher import AES
# AES ecb
# pip3 install pycryptodome
# pip install pybase64

# Encryption For Transmission Security
BLOCK_SIZE = 16  # Bytes
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

def aesEncrypt(key, data_bytes):
    '''
    AES的ECB模式加密方法
    :param key: 密钥 (str)
    :param data_bytes: 需要加密的东西 (bytes)
    :return:密文 (bytes)
    '''
    key = key.encode('utf8')
    str_un_padded = base64.b64encode(data_bytes).decode()
    # 字符串补位
    str_padded = pad(str_un_padded)
    cipher = AES.new(key, AES.MODE_ECB)
    # 加密后得到的是bytes类型的数据，使用Base64进行编码,返回byte字符串
    encryDataBytes = cipher.encrypt(str_padded.encode())
    return encryDataBytes


def aesDecrypt(key, encryDataBytes):
    '''
    :param key: 密钥
    :param data: 密文 (bytes)
    :return: 加密前的东西 (bytes)
    '''
    key = key.encode('utf8')
    cipher = AES.new(key, AES.MODE_ECB)
    # 去补位
    str_padded = cipher.decrypt(encryDataBytes).decode()
    str_un_padded = unpad(str_padded)
    data_bytes = base64.b64decode(str_un_padded.encode())
    return data_bytes
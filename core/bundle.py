import io
from hashlib import sha256
from Crypto.Cipher import AES


class Bundle:
    def __init__(self, bundle: io.BytesIO) -> None:
        self.bundle: bytes = bundle
        self.magicWord: bytes
        self.version: int
        self.headerSize: int
        self.encryptionMode: int
        self.keyLength: int
        self.encryptedLength: int
        self.aesKey: bytes
        self.iv: bytes
        self.setup(self.bundle)

    def setup(self, bundle: io.BytesIO):
        self.magicWord = bundle.read(4)
        if self.magicWord != b"NKAB" and self.magicWord != b"Unit":
            raise ("Not support file!")
        if self.magicWord == b"NKAB":
            self.version = int.from_bytes(
                bundle.read(4), byteorder="little", signed=False
            )
            self.headerSize = (
                int.from_bytes(bundle.read(2), byteorder="little", signed=True) + 100
            )
            self.encryptionMode = (
                int.from_bytes(bundle.read(2), byteorder="little", signed=True) + 100
            )
            self.keyLength = (
                int.from_bytes(bundle.read(2), byteorder="little", signed=True) + 100
            )
            self.encryptedLength = (
                int.from_bytes(bundle.read(2), byteorder="little", signed=True) + 100
            )

            self.aesKey = self.shaValue(bundle.read(self.keyLength))
            self.iv = bundle.read(self.keyLength)
        else:
            bundle.seek(0)
            self.aesKey = b"ModdedNIKKEAsset"
            self.keyLength = len(self.aesKey)
            self.iv = self.shaValue(bundle.read())[0:16]
            bundle.seek(0)
            self.magicWord = b"NKAB"
            self.version = 1
            self.headerSize = 48
            self.encryptionMode = 0
            self.encryptedLength = 128

    def shaValue(self, value: bytes) -> bytes:
        shaObject = sha256()
        shaObject.update(value)
        return shaObject.digest()

    def decryptBundle(self) -> io.BytesIO:
        encryptedData: bytes = self.bundle.read(self.encryptedLength)
        decryptor = AES.new(self.aesKey, AES.MODE_CBC, iv=self.iv)
        decryptedData = decryptor.decrypt(encryptedData)
        return io.BytesIO(decryptedData + self.bundle.read())

    def encryptBundle(self) -> io.BytesIO:
        decryptedData: bytes = self.bundle.read(self.encryptedLength)
        encryptor = AES.new(self.shaValue(self.aesKey), AES.MODE_CBC, iv=self.iv)

        encryptedData: bytes = b""
        encryptedData += self.magicWord
        encryptedData += self.version.to_bytes(4, byteorder="little", signed=False)
        encryptedData += (self.headerSize - 100).to_bytes(
            2, byteorder="little", signed=True
        )
        encryptedData += (self.encryptionMode - 100).to_bytes(
            2, byteorder="little", signed=True
        )
        encryptedData += (self.keyLength - 100).to_bytes(
            2, byteorder="little", signed=True
        )
        encryptedData += (self.encryptedLength - 100).to_bytes(
            2, byteorder="little", signed=True
        )
        encryptedData += self.aesKey
        encryptedData += self.iv
        encryptedData += encryptor.encrypt(decryptedData)
        encryptedData += self.bundle.read()
        return io.BytesIO(encryptedData)

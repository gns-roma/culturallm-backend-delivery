import hashlib
import os

# generate a casual salt of "byte" bytes
def get_salt(byte: int) -> bytes:
    return os.urandom(byte)

# it computes the hash of pwd + salt
def hash_password(password, salt) -> str:
    pwd_hash: str = hashlib.sha256(salt + password.encode()).hexdigest()
    return pwd_hash

# checks wether the password is correct or not
def verify_password(stored_hash, stored_salt, provided_password) ->bool:
    pwd_hash = hashlib.sha256(stored_salt + provided_password.encode()).hexdigest()
    return pwd_hash == stored_hash

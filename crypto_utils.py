from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
import shutil
import os
import tempfile
import atexit
import time

# ----------------- KEY MANAGEMENT -----------------
KEY_PATH = Path("secret.key")

def generate_key(path: str = "secret.key") -> bytes:
    """Generate a new encryption key and save to file."""
    key = Fernet.generate_key()
    Path(path).write_bytes(key)
    return key

def load_key(path: str = "secret.key") -> bytes:
    """Load the encryption key; auto-generate if missing."""
    p = Path(path)
    if not p.exists():
        return generate_key(path)
    return p.read_bytes()

def delete_key(path: str = "secret.key") -> bool:
    """Delete the encryption key file if it exists."""
    p = Path(path)
    if p.exists():
        p.unlink()
        return True
    return False

# ----------------- ENCRYPT / DECRYPT FILES -----------------
def encrypt_file(src_path: str, key: bytes, dst_path: str = None):
    """Encrypt a file using Fernet."""
    if not os.path.exists(src_path):
        return
    f = Fernet(key)
    data = Path(src_path).read_bytes()
    token = f.encrypt(data)
    Path(dst_path or src_path).write_bytes(token)

def decrypt_file(src_path: str, key: bytes, dst_path: str = None):
    """Decrypt a file; raises InvalidToken if invalid."""
    f = Fernet(key)
    token = Path(src_path).read_bytes()
    data = f.decrypt(token)
    Path(dst_path or src_path).write_bytes(data)

def safe_decrypt_file(src_path: str, key: bytes, dst_path: str):
    """Try to decrypt; if not encrypted, copy plain file."""
    if not os.path.exists(src_path):
        return
    try:
        f = Fernet(key)
        token = Path(src_path).read_bytes()
        data = f.decrypt(token)
        Path(dst_path).write_bytes(data)
    except (InvalidToken, Exception):
        # Not encrypted or error -> copy file directly
        shutil.copy2(src_path, dst_path)

def ensure_encrypted_backup(src_path: str, key: bytes):
    """Create encrypted backup of the file."""
    if not os.path.exists(src_path):
        return
    backup_path = f"{src_path}.enc"
    encrypt_file(src_path, key, dst_path=backup_path)

# ----------------- TEMPORARY FILE CLEANUP -----------------
_temp_files = set()

def register_temp_file(file_path: str):
    """Register a temporary file for cleanup."""
    _temp_files.add(file_path)

def cleanup_temp_files():
    """Clean up all registered temporary files."""
    for file_path in _temp_files.copy():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            _temp_files.discard(file_path)
        except Exception:
            pass  # Ignore cleanup errors

def safe_temp_file():
    """Create a safe temporary file that will be cleaned up."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    register_temp_file(path)
    return path

# Register cleanup function to run on exit
atexit.register(cleanup_temp_files)

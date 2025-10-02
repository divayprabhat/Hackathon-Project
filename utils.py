import os
import bz2
import urllib.request
from pathlib import Path

def download_and_extract(url, output_path):
    """Download and extract model files if they don't exist."""
    if os.path.exists(output_path):
        return
    
    bz2_path = output_path + '.bz2'
    if not os.path.exists(bz2_path):
        print(f'[INFO] Downloading: {url}')
        try:
            urllib.request.urlretrieve(url, bz2_path)
        except Exception as e:
            print(f'[ERROR] Failed to download {url}: {e}')
            return
    
    print(f'[INFO] Extracting {bz2_path}')
    try:
        with bz2.BZ2File(bz2_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                f_out.write(f_in.read())
        # Clean up compressed file
        os.remove(bz2_path)
    except Exception as e:
        print(f'[ERROR] Failed to extract {bz2_path}: {e}')

import os


def guess_file_format(filename):
    """Try to guess mgf or msp file format"""

    ext = os.path.splitext(filename)[1].lower()
    if ext in ('.mgf', '.msp'):
        return ext[1:]

    try:
        with open(filename, 'r') as f:
            head = next(f)
            if head.startswith('BEGIN IONS'):
                return 'mgf'
            elif head.startswith('NAME:'):
                return 'msp'
    except UnicodeDecodeError:
        return

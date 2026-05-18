import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
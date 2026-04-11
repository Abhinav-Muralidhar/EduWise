import os
from jinja2 import Environment, FileSystemLoader

try:
    env = Environment(loader=FileSystemLoader('app/templates'))
    for root, dirs, files in os.walk('app/templates'):
        for file in files:
            if file.endswith('.html'):
                try:
                    env.get_template(file)
                    print(f'{file}: OK')
                except Exception as e:
                    print(f'{file}: ERROR - {e}')
except Exception as e:
    print(f"Failed to setup jinja2: {e}")

# app/templates.py

import os
from fastapi.templating import Jinja2Templates

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, '..', 'frontend', 'templates')
templates = Jinja2Templates(directory=templates_dir)

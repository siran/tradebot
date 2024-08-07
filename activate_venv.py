import os

path_this_file = os.path.dirname(os.path.realpath(__file__))

venv = f'{path_this_file}/venv/bin/activate_this.py'
if os.path.isfile(venv):
    exec(open(venv).read(), dict(__file__=venv))
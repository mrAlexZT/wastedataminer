#!/bin/bash
kill -9 $(ps -aux | grep '[p]ython app.py' | awk '{print $2}')

cd /DIRECTORY_NAME
source /DIRECTORY_NAME/python_env/bin/activate
python3 app.py

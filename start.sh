#!/bin/bash

python main.py
git pull
pip install --no-cache-dir -r requirements.txt

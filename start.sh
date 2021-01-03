#!/bin/bash

git pull
pip install --no-cache-dir -r requirements.txt
python main.py

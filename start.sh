#!/bin/sh

if [ ! -d "FlagBot" ]; then
git clone https://github.com/FlagBrew/FlagBot.git
fi
cd FlagBot
git pull
pip uninstall -r requirements.txt
pip install --no-cache-dir --upgrade -r requirements.txt
python main.py

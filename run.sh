#!/usr/bin/env bash
echo "Redirecting all logs into ./torrents/$1.log"
python3 main.py $1 2>&1 | tee "./torrents/$1.log"

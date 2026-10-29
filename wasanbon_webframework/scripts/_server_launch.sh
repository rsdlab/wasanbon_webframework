#!/bin/bash

source ~/.bashrc

nohup uvicorn wasanbon_webframework.main:app --port 8000 --host 0.0.0.0 >/dev/null 2>&1 &

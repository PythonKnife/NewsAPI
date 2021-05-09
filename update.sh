#!/bin/bash

source venv/bin/activate
venv/bin/python -c 'import main; main.update_data()'

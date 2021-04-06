#!/bin/bash
isort .
black . --line-length 120
echo "ruby <3"

#!/bin/bash
isort -rc .
black . --line-length 120

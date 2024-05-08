#!/bin/bash

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null
then
    echo "pre-commit could not be found, installing..."
    pip install pre-commit
fi

# Install the pre-commit hooks from the configuration file
pre-commit install

# Comment the next line if you don't want to automatically run pre-commit on all files
pre-commit run --all-files

echo "Pre-commit setup is complete."

#!/bin/bash

# Make the pre-commit script executable
chmod +x pre-commit

# Create the symlink to the pre-commit hook
ln -sf "$(pwd)/pre-commit" "$(pwd)/.git/hooks/pre-commit"

echo "Git hooks installed successfully!" 
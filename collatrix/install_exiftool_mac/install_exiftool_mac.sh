#!/bin/bash

# Set the working directory to the folder containing the script
cd "$(dirname "$0")"

# Download and extract ExifTool
gzip -dc Image-ExifTool-12.76.tar.gz | tar -xf -

# Enter the ExifTool directory
cd Image-ExifTool-12.76

# Build and install ExifTool
perl Makefile.PL
make test
sudo make install

# Pause to see the output when double-clicked
read -p "Press Enter to exit"
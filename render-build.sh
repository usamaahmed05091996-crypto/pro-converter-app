#!/usr/bin/env bash
# Swap file banayein (512MB ki virtual RAM)
fallocate -l 512M /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
# Baki commands...
apt-get update && apt-get install -y poppler-utils
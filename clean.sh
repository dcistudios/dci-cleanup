#!/bin/bash
clear

# Set Color to Cyan
echo -e "\e[36m"

# DCI Logo
echo "  :::::::::   ::::::::  :::::::::: "
echo "  :+:    :+: :+:    :+:    :+:     "
echo "  +:+    +:+ +:+           +:+     "
echo "  +#+    +:+ +#+           +#+     "
echo "  +#+    +:+ +#+           +#+     "
echo "  #+#    #+# #+#    #+#    #+#     "
echo "  #########   ########     ###     "
echo "                                   "
echo "     [ DCI STUDIOS PRESENTS ]      "
echo "     >> SYSTEM: SPECTRE-CLN <<     "
echo -e "\e[0m"

# Slow loading simulation
echo -n "Initializing"
for i in {1..3}; do echo -n "."; sleep 0.4; done
echo -e "\n"

echo "Starting cleanup protocol..."
sleep 0.5

# Run the cleanup
python3 discord_cleanup.py

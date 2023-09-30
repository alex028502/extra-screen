#!/usr/bin/env bash

set -e


# screen -S aux -d -m
# echo this is your typing terminal
# echo please go like this in your viewing terminal
# echo screen -r aux

while read -rsn1 input; do
    echo stuffing "$input"
    screen -S $1 -X stuff "$input"
done

#!/bin/bash
for filename in user_manual/images/icons/*.svg;
    do rsvg-convert -h 18 -f png -o "${filename%.*}.png" $filename;
done

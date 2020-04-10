mkdir "images/icons_scaled";
for filename in images/icons/*.svg;
    do rsvg-convert -h 18 -f svg -o images/icons_scaled/${filename##*/} $filename;
done

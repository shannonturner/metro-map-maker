#! /bin/bash

# Automatically reduces the quality of and resizes PNG images in the specified folder. Requires ImageMagick.

# Usage example: /Users/shannon/Dropbox/github/metro-map-maker/images/optimize-images.sh /Users/shannon/Dropbox/github/metro-map-maker/images/___unoptimized/

# Note: To avoid optimizing an image more than once, begin in the "___unoptimized" folder and once optimization has occurred, if the results are good, move the image into the parent images folder

for i in ${1%/*}/*.png;
do
    echo "Optimizing image: $i";
    convert $i -strip -resize 200x200 -colors 32 $i
done

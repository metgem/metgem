file="${1}"
iconset="$(mktemp -d /tmp/iconsetXXXX)"
output_icon="main.icns"

echo "${file}"
echo "${iconset}"
echo "${output_icon}"

for size in {16,32,128,256,512}; do
  convert -density 384 -background transparent "${file}" -resize "!${size}x${size}" "${iconset}/icon_${size}x${size}.png"
  convert -density 384 -background transparent "${file}" -resize "!$((size * 2))x$((size * 2))" "${iconset}/icon_${size}x${size}@2x.png"
done

mv "${iconset}" "${iconset}.iconset"
iconutil --convert icns "${iconset}.iconset" --output "${output_icon}"

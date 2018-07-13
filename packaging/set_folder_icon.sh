pushd $2
echo "Read 'icns' (-16455) \"$1\";" > Icon.rsrc
Rez -a Icon.rsrc -o $3/Icon$'\r'
SetFile -a C $3
SetFile -a V $3/Icon$'\r'
popd
inotifywait -r -m -e close_write . |
while read path action file; do
    if [[ "$file" =~ .*rst$ ]]; then
        make html
    elif [[ "$file" =~ .*py$ ]]; then
        make clean && make html
    fi
done 

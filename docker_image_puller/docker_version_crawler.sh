#!/bin/bash

RELATIVE_PATH="../resources"
RESOURCES_PATH=${PWD}'/'$RELATIVE_PATH
FILE=$RESOURCES_PATH/"docker_hub_library.csv"

while IFS=',' read -r provider cms;
do
    echo "Provider: $provider, CMS: $cms"

    page=1
    result_directory=$RESOURCES_PATH"/docker_hub_library_version"
    result_file=$result_directory"/"$cms"_version"
    mkdir $result_directory
    touch $result_file
    (
        while true;
        do
            result=$(curl -s "https://hub.docker.com/v2/repositories/$provider/$cms/tags?page_size=100&page=$page")
            

            # echo "$result" | jq -r '.results[].name | match("[0-9]+(\\.[0-9]+)+") | .string' >> $result_file
            echo "$result" | jq -r '.results[].name' | grep -E '^[0-9]+(\.[0-9]+)*$'

            next=$(echo "$result" | jq -r '.next')
            if [ "$next" = "null" ]; then
                break
            fi
            page=$((page + 1))
        done
    ) | sort -V -u > "$result_file"
done < <(tail -n  +1 "$FILE") 
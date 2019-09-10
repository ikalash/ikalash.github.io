#!/bin/bash

now=$(date +"%Y%m%d")
FILE=ctest-$now.json
echo $FILE
if test -f "$FILE"; then
  echo "$FILE file exists"
  now=$(date +"%m_%d_%Y")
  echo $now
  mv Blob_PerfTestsBlake.html Blob_PerfTestsBlake_$now.html
  git add Blob_PerfTestsBlake_$now.html
  git commit -m "Checking in jupyter notebook from $now" 
  git push
  rm html_entry 
  echo "<li><p><strong><a href="blake_nightly_data/Blob_PerfTestsBlake_$now.html">$now</a></strong>.</p>" >& html_entry
else  
  echo "$FILE does not exist! Not Jupyter notebook in repo."
fi

#/bin/bash

CSV=$1 # use .csv as argument to this script
ALG_TYPE=$2 
TIMES_TO_RUN=100

for k in {1..10}
do
  python3 deanonymize.py $CSV $ALG_TYPE random $k $TIMES_TO_RUN
done

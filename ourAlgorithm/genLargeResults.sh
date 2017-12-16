#/bin/bash

CSV=$1 # use .csv as argument to this script
TIMES_TO_RUN=100

for alg in "simple" "directed"
do
  for k in {1..10}
  do
    python3 ourAlgorithm.py $CSV $alg random $k $TIMES_TO_RUN
  done
done

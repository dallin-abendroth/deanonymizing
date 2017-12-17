# deanonymizing
CS 6150 Project

Using Python 3 and [NetworkX](http://networkx.github.io/) ([docs](https://networkx.github.io/documentation/stable/)) 

`pip3 install networkx`

Implementing the algorithm described by "Wherefore Art Thou R3579X? Anonymized Social Networks, Hidden Patterns, and Structural Steganography" by Lars Backstrom, Cynthia Dwork, and Jon Kleinberg

Applying and improving this algorithm to work with datasets representing a social network with "weighted" edges:

* [Bitcoin OTC](https://snap.stanford.edu/data/soc-sign-bitcoinotc.html)

* [Mobility Networks in Colombia](https://icon.colorado.edu/)

Both datasets are available in this repository as `.csv` files.

## Usage 

```
  python ourAlgorithm/deanonymize.py [csv file to use] [simple|directed] random [size of coalition] 
  python ourAlgorithm/deanonymize.py [csv file to use] [simple|directed] random [size of coalition] [times to run]
  python ourAlgorithm/deanonymize.py [csv file to use] [simple|directed] given_coalition [coalition member 1] ... [coalition member N]
  
    NOTE: coalition must strictly consist of a 'root' node and its neighbors
```

There is a bash script that can be run to generate results for increasing numbers of k:

`ourAlgorithm/genLargeResults.sh [csv file to use] [simple|directed]` 

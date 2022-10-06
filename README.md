# IRIS utils

Usefull scripts for the IRIS project

## Setup
You can import it, in each of the other projects, as a submodule
* ``> git submodule add https://github.com/n3ssuno/iris-utils.git src/utils``
* ``> git commit -m "Add iris-utils submodule"``
* ``> git push``

Also run, in the Python, the following commands:
* ``> import nltk``
* ``> nltk.download('punkt') # used by nlp.py``
* ``> nltk.download('words') # used by award_id.py``
* ``> nltk.download('wordnet') # used by award_id.py``

## Acknowledgements
The authors thank the EuroTech Universities Alliance for sponsoring this work. Carlo Bottai was supported by the European Union's Marie Skłodowska-Curie programme for the project Insights on the "Real Impact" of Science (H2020 MSCA-COFUND-2016 Action, Grant Agreement No 754462).

# DblpSearchEngine

my personal search engine for the dblp database. \
in development...

# Testing
the application is tested on windows 10, but linux should be also supported...

# Language supported:

f-t-s : ([field:] search-pattern) \
search-pattern : keyword | “phrase” \
field: pub-search | venue-search \
pub-search : pub-ele[.pub-field] \
pub-ele: publication | article | incollection | inproceedings | phThesis | masterThesis \
pub-field: author | title | year \
venue-search: venue[.venue-field] \
venue-field: title | publisher 

# Requirements
- python3 
- python3-pip
- whoosh

# Installation step (windows)
- download and install python3.7.3 from the official site (https://www.python.org/downloads/)
- open a terminal (power-shell)
- run the following command: pip.exe install whoosh

# Installation step (linux)
- open a terminal
- run the following command: pip3 install whoosh

# Run  (linux)
- download the dblp xml database from the following site: https://dblp.uni-trier.de/xml/
- extract "dblp.xml.gz" and move the file "dblp.xml" to the project parent directory 
- open a terminal
- go to the project directory
- run: python3 main.py
 
 # Run  (windows)
- download the dblp xml database from the following site: https://dblp.uni-trier.de/xml/
- extract "dblp.xml.gz" and move the file "dblp.xml" to the project parent directory 
- open a terminal (power-shell)
- go to the project directory
- run: python.exe .\main.py





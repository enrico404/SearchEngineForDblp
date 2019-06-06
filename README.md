# dblpSearchEngine

my personal search engine for the dblp database.
in development...

# testing
move the file "test.xml" to the parent directory of the project folder

# how to use

f-t-s : ([field:] search-pattern) \
search-pattern : keyword | “phase” \
field: pub-search | venue-search \
pub-search : pub-ele[.pub-field] \
pub-ele: publication | article | incollection | inproc | phThesis | masterThesis \
pub-field: author | title | year \
venue-search: venue[.venue-field] \
venue-field: title | publisher \

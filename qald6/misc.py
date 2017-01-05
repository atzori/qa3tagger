import pprint; pp = pprint.PrettyPrinter(indent=4,width=1)
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from disk_memoize import memoize_to_disk
from nltk.stem import WordNetLemmatizer
import re

# patterns

lemmatizer = WordNetLemmatizer()
p = re.compile(r'[^A-Za-z0-9\']+')
multi_spaces = re.compile(r'\s+')

re_clean_spaces = re.compile(r'(^\s*)|(\s*$)|\s(\s*)')

def normalize(s,synonyms=True):
	"transform a sentence into a pair: a cleaner sentence and tokens"

	# lowercase
	s = s.lower()

	# cleanup
	s = s.replace('\\r',' ')
	s = s.replace('\\n',' ')
	s = p.sub(' ',s)	
	s = multi_spaces.sub(' ',s)	
	s= s.strip()

	# tokenize
	words = word_tokenize(s)

	# lemmatize
	words = [lemmatizer.lemmatize(w, pos='n') for w in words]
	words = [lemmatizer.lemmatize(w, pos='v') for w in words]
	if synonyms: words = [synonyms_map[w] if w in synonyms_map else w for w in words]

	words = [w for w in words if w not in stopwords_map]
	s = ' '.join(words)
	#s = s.replace(" 's ","'s ")
	s = s.replace(" 's "," ")
	s = s.replace(" , "," ")
	return s


def clean_str(s,synonyms=True):
	"transform a sentence into a pair: a cleaner sentence and tokens"

	# lowercase
	s_preprocessed = s.lower()

	# cleanup
	s_preprocessed = p.sub(' ',s_preprocessed)	
	s_preprocessed = s_preprocessed.strip()

	# tokenize
	words = word_tokenize(s_preprocessed)

	# lemmatize
	words = [lemmatizer.lemmatize(w, pos='n') for w in words]
	words = [lemmatizer.lemmatize(w, pos='v') for w in words]
	if synonyms: words = [synonyms_map[w] if w in synonyms_map else w for w in words]

	words = [w for w in words if w not in stopwords_map]
	s_preprocessed = ' '.join(words)
	#s_preprocessed = s_preprocessed.replace(" 's ","'s ")
	s_preprocessed = s_preprocessed.replace(" 's "," ")
	s_preprocessed = s_preprocessed.replace(" , "," ")
	return s_preprocessed , s_preprocessed.split() #words


def line2triple(line):
	"transform a rdf triple string into a 3-way array"
	triple = line.strip('. \n\r').split(' ',2) 	# triplify
	triple[2] = triple[2].strip('"')	
	return triple

def find_uri(keywordPhrase,ignorecase=True,files=['labels.nt','comments.nt']):
	"given a phrase returns pairs (uri,string_label) matching the phrase"
	if ignorecase: keywordPhrase = keywordPhrase.lower()
	matches = []
	for f in [open(f) for f in files]:
		for line in f:
			triple = line2triple(line)
			tomatch = triple[2]
			if ignorecase: tomatch = tomatch.lower()
			if keywordPhrase in tomatch: matches += [(triple[0],triple[2])] # in line:
	return matches

def cleanup_question(q):
	return q.replace('?',' ').strip() # cleanup

def ngram(sentence,n=2):
	"get ngram words of a sentence"
	s = cleanup_question(sentence).split()
	return [ s[i:i+n] for i in range(len(s)-n+1) ]

def find_spots(sentence,quiet=False,verbose=False,files=['labels.nt','comments.nt']):
	"""return a dictionary of spots (phrases in the sentence) 
		with corresponding (matching) uris and scores"""
	from math import log
	spots = {}
	for n in range(4,0,-1):
		if not quiet: print '\nsize %d' % n
		for c in ngram(sentence,n):
			s = ' '.join(c)
			matches = find_uri(s,files=files)
			if not quiet: print '.',
			if len(matches)>0: 
				# match(es) found for the current ngram s
				if verbose: print '\n',s, len(matches)
				matches = [(m[0],m[1],dist(s,m[1])) for m in matches]
				matches = sorted(matches,key=lambda m: m[2])
				res = [ (m[0],m[1],
					#dist(sentence,m[1]), 
					#1.0/(1.0+log(1+dist(sentence,m[1])) ),
					m[2],  
					1.0/(1+log(1+m[2]))  ) for m in matches[:10]]
				if verbose: pp.pprint(res)
				spots[s] = res
	if verbose: print '====================='; pp.pprint(spots)
	return spots

def dist(s1, s2, ignorecase=True): 
	if ignorecase:
		s1,s2 = s1.lower(), s2.lower()
	return levenshtein(s1, s2)

def levenshtein(s1, s2):
	"edit distance from Wikipedia"
	if len(s1) < len(s2):
		return levenshtein(s2, s1)

	# len(s1) >= len(s2)
	if len(s2) == 0:
		return len(s1)

	previous_row = range(len(s2) + 1)
	for i, c1 in enumerate(s1):
		current_row = [i + 1]
		for j, c2 in enumerate(s2):
		    insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
		    deletions = current_row[j] + 1       # than s2
		    substitutions = previous_row[j] + (c1 != c2)
		    current_row.append(min(insertions, deletions, substitutions))
		previous_row = current_row

	return previous_row[-1]

def sparql(query,endpoint='http://cubeqa.aksw.org/sparql'):
	from SPARQLWrapper import SPARQLWrapper, JSON

	sparql = SPARQLWrapper(endpoint)
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	r = []
	for result in results["results"]["bindings"]:
		r += [result["ds"]["value"]] #print(result["ds"]["value"])
	return r

def top(spots,threshold=0.5):
	res = []
	keys = sorted([a for a in spots], key = lambda e: -len(e))
	for k in keys:
		for m in spots[k]:
			if m[-1]> threshold:
				x = (k, spots[k][0][0], spots[k][0][-1])
				if x not in res: res += [x]
	return res


########################################################

stopwords_map = {}
for s in stopwords.words('english'):
	stopwords_map[s] = None

synonyms = [
	['earning','revenue'],
	['expenditure','spending'],
	['admin','admins']
]
synonyms_map = {}

for synset in synonyms:
	clean_synset = sorted([ clean_str(s,synonyms=False)[0] for s in synset])
	for c in clean_synset:
		synonyms_map[c] = clean_synset[0]



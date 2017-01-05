import re
import misc


def read_prefixes(filename='prefixes.txt'):
    pairs = [line.strip().split() for line in open(filename) if line.strip() is not ""] # for a in line.strip().split('\t')]
    return [{'prefix':pair[0], 'uri':pair[1]} for pair in pairs]

def read_data(filename='qald-6-train-datacube.json',prefixes_filename='prefixes.txt'):
    def sparql(q):
        if 'pseudo' in q:
            return q['pseudo']
        else: return q['sparql']

    import json, re

    # load dataset
    train = json.load(open(filename))

    # get (q)uestions and (s)parql query
    try:
	    questions = [ {'q':q['question'][0]['string'].strip(), 's':sparql(q['query']), 'id':q['id'].strip()} 
                     for q in train['questions'] ]
    except:
	    questions = [ {'q':q['question'][0]['string'].strip(), 's':'', 'id':q['id'].strip()} 
                     for q in train['questions'] ]


    prefixes = read_prefixes(prefixes_filename)
    for q in questions:        
        # get (d)ataset
        try:
            q['d'] = 'finland-aid' if 'from' not in q['s'] else re.search(' from <http://[^>]*/([^/>]*)>', q['s']).group(1)
        except: pass

        # get (s)parql query e(x)tended
        try:
            q['sx'] = q['s']
            for p in prefixes:
                q['sx'] = re.sub('\\b'+p['prefix']+':([a-zA-Z0-9#-&+-_,]*)\\b',
                        '<'+p['uri']+'\\1>',q['sx'])	
        except: pass
        # get (u)ris
        q['u'] = re.findall('<https?://[^>]*>', q['sx']) #.group(1)
    return questions


def dataset_labels(filename='./dataset_labels.json'):
	sparql_query = """
	select * {
		?s a qb:DataSet.
		optional {
		    ?s rdfs:label ?l
		}
		optional {
		    ?s rdfs:comment ?c 
		}
	}"""

	# run previous query against http://cubeqa.aksw.org/sparql and get the file 'dataset_labels.json':
	import json
	from qald6.misc import clean_str
	dataset_labels = json.load(open(filename, 'r'))['results']['bindings']
	dataset_labels = [ (t['s']['value'],t['l']['value'],t['c']['value']) for t in dataset_labels]
	dataset_labels = [ (s[s.rfind('/')+1:],clean_str(l1)[0],clean_str(l2)[0]) for s,l1,l2 in dataset_labels]
	dl = {}
	for s,l1,l2 in dataset_labels:
		l1 , l2 = re.sub(misc.re_clean_spaces,'',l1) , re.sub(misc.re_clean_spaces,'',l2)
		dl[s] = {'label':l1,'comment':l2, 'text': l1+' '+l2}
	return dl


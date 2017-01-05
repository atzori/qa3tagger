from disk_memoize import memoize_to_disk
from misc import ngram
import qald6
from qald6.misc import clean_str , normalize
import re, collections
import cgi
import datetime
from qald6 import train, measure
import sys

p = re.compile(r'\s*(<[^<]+>)\s+(<[^<]+>)\s+("(.*)"[^"]*)\s*.\s*[\r\n]*')


# finding all labels => triple mapping
#@memoize_to_disk
def labels_map_slow(dataset_filename,fast=True):
	Q = '"'
	labels_map = collections.defaultdict(lambda: [])

	with open(dataset_filename) as infile:
		for line in infile:
			# get uri/label pairs
			if Q not in line: continue # skipping non-literals
			triple = tuple( line.strip('. \n\r').split(' ',2) )
			if not triple[2][0]==Q: continue # skipping non-literals (should not be necessary)
			label = triple[2].strip()
			label = label[1:label.rfind(Q)]
			label = clean_str(label)[0]
			if re.search( r'observation [\da-zA-Z]{10,50}', label): continue # skip ugly obs
			if label.strip() == '': continue
			if not fast or len(labels_map[label])==0: 
				labels_map[label] += [triple]
	return labels_map


@memoize_to_disk
def labels_map(dataset_filename,fast=True):
	labels_map = collections.defaultdict(lambda: [])

	# group 0 matches all
	# group 1 matches the first url
	# group 2 matches the second url
	# group 3 matches the third element (label+optional datatype)
	# group 4 matches the label only

	seen = {}

	with open(dataset_filename) as infile:
		for line in infile:
			#print line
			# get uri/label pairs
			m = p.match(line)
			if not m: continue # skipping non-literals
			label = m.group(4)
			if re.search( r'observation [\da-zA-Z]{10,50}', label): continue # skip ugly obs
			if fast and label in seen: continue
			else: seen[label] = None
			label = clean_str(label)[0]
			if not fast or len(labels_map[label])==0: 
				labels_map[label] += [(m.group(1),m.group(2),m.group(3))]
	return labels_map



def labels(fin):
	# group 0 matches all
	# group 1 matches the first url
	# group 2 matches the second url
	# group 3 matches the third element (label+optional datatype)
	# group 4 matches the label only

	for line in fin:
		m = p.match(line)
		if not m: continue # skipping non-literals
		label = m.group(4)
		if re.search( r'observation [\da-zA-Z]{10,50}', label): continue # skip ugly obs
		#if label in seen: continue
		#else: seen[label] = None
		label = normalize(label)
		if label:
			yield label

#tagged_sentence = preprocessed_question
#@memoize_to_disk
def find_matching_labels(preprocessed_question,labels, presorted=False):

	found_labels = []

	#choose strategy
	if False: #len(preprocessed_question.split())*10 > len(labels):
		if not presorted: labels = sorted(labels, key=lambda e: -len(e))
		for l in labels:
			if re.search( "\\b%s\\b" % re.escape(l), preprocessed_question):
				found_labels.append(l)
	else:
		for n in range(7,0,-1):
			#print '\nsize %d' % n
			for c in ngram(preprocessed_question,n):
				s = ' '.join(c)
				if (s in labels): 
					found_labels.append(s)
	return sorted(found_labels, key=lambda e: -len(e))



def render(question,preprocessed_question,found_labels,labels_map,html=True):
	question = question.strip()
	ending_question_mark = question[-1] == "?"
	tagged = question.replace('?','')
	tagged = [clean_str(q)[0] for q in question.split()]

	mapping = [i for i, e in enumerate(tagged) if e != '']
	result = question.strip().replace('?','').split()

	label_positions = {} # positions in number of words
	for label in found_labels:
		#print label
		s = preprocessed_question.find(label)
		words_before = len(preprocessed_question[:s].split())
		words_last = words_before + len(label.split())
		found = False
		for l in label_positions:
			a,b = label_positions[l]
			if set(range(a,b)).intersection(set(range(words_before,words_last))):
				found = True
				break
		if not found:
			label_positions[label]= (words_before, words_last) #begin, end
    
	for label in found_labels:
		#print label
		if label not in label_positions: continue

		posinfo = label_positions[label]
		#print posinfo
		pos = posinfo[0]
		#print pos
		end_pos = posinfo[1]-1 #pos+len(label.split())
		#print end_pos
		pos1 = mapping[pos]
		#print pos1
		end_pos1 = mapping[end_pos]
		title = labels_map[label][0]
		if html:
			title = cgi.escape(str(title), quote=True) 
			result[pos1] = '<a title="%s">%s' % ( title ,result[pos1])
			result[end_pos1] = result[end_pos1] + '</a>'
		else:
			result[pos1] = '\n%s' % (result[pos1])
			result[end_pos1] = result[end_pos1] + '\t%s\n' % '\t'.join([t for t in title]) 

	return ' '.join(result) + '?' if ending_question_mark else ''


def tag(question, test_set=None,verbose=True):
	"""Returns an object with the tagged question. Format:
		{
			question: string # input question
			correct_dataset: string # name of the correct dataset
			results: [ 
				# the first object is the one automatically by the system
				{
					dataset: string ,
					is_correct_dataset: boolean ,
			
				},
				.... # in case other solutions may follow
			]
		}

	"""
	training_set = train.read_data()
	test_set = test_set or training_set # if not specified then all instances

	dl = train.dataset_labels()

	res = {
		'question' : question,
		'correct_dataset': None,
		'results': []
	}

	# correct dataset
	correct_dataset = [t['d'] for t in training_set if question.strip().lower() == t['q'].strip().lower()]
	if correct_dataset: 
		correct_dataset = correct_dataset[0]
		res['correct_dataset'] = correct_dataset

	final = []
	for dataset in set([t['d'] for t in test_set]):

		# loading dataset labels
		if verbose: print dataset; sys.stdout.flush()
		#timing = datetime.datetime.now()
		labels_map = qald6.tag.labels_map('benchmarkdatasets/%s.nt' % dataset,fast=True)
		#print "(%.3fs) " % (datetime.datetime.now() - timing).total_seconds() ,

		preprocessed_question , tokens = clean_str(question)
		found_labels = qald6.tag.find_matching_labels(preprocessed_question,labels_map,presorted=True)

		reminder = measure.reminder(preprocessed_question,found_labels)
		words_missing = set(reminder[0].split())
		extra_sentence , extra_words = clean_str(dataset)
		words_missing2 = set([w for w in words_missing if (w not in extra_words) and
								w not in extra_sentence])
		words_missing2 -= set(['use','wa','how','much','do','per'])

		try:
			extra_words += dl[dataset]['text'].split()
		except:
			print dataset
			print 'NOT FOUND'
			raise Exception('not found')
		words_missing3 = set([w for w in words_missing2 if w not in extra_words])
		wordup = len(words_missing2) -len(words_missing3)

		final.append ( tuple([
			dataset, 
			len(words_missing2)-wordup*1.1,
			len(words_missing),
			' '.join(words_missing2), 
			' '.join(words_missing3),
			{ # other tmp data
				'preprocessed_question': preprocessed_question,
				'found_labels': found_labels,
				'labels_map': labels_map
			}
		]))


	final = sorted(final, key=lambda e: e[1])
	best = [r for r in final[:10]]
	data = best[0][-1]
	preprocessed_question,found_labels,labels_map = data['preprocessed_question'], data['found_labels'], data['labels_map']
	best = [r[:-1] for r in best]

	if best[0][0]==correct_dataset and best[0][1] < best[1][1]-0.8:
		if verbose: print '\n', 'OK', best
	elif (-best[0][1] + best[1][1])<0.8:
		similar = [c for c in best if (-best[0][1] + c[1])<0.8]
		similar = sorted(similar,key=lambda e: e[2])
		if verbose: print '\n', 'NOT SURE', len(similar), 
		if similar[0][2]<similar[1][2] and similar[0][0] ==correct_dataset:
			if verbose: print 'OK', 
		elif similar[0][2]==similar[1][2]:
			if verbose: print 'NOT SURE',
		else:
			if verbose: print 'MISTAKE',    
		if verbose: print similar
	else: 
		if verbose: print '\n', 'MISTAKE', best


	solution_found = {
		'dataset': best[0][0],
		'is_correct_dataset': (best[0][0]==correct_dataset),
		'text_tags': qald6.tag.render(question,preprocessed_question,found_labels,labels_map,html=False),
		'html_tags': qald6.tag.render(question,preprocessed_question,found_labels,labels_map,html=True)
	}

	res['results'].append(solution_found)
	return res





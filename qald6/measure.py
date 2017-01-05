from nltk.corpus import stopwords
import re
from disk_memoize import memoize_to_disk

def reminder(s,found_labels):
	reminder = s
	for l in sorted(found_labels, key=lambda e: -len(e)) + stopwords.words('english'):
		reminder = re.sub('\\b%s\\b' % l, '', reminder)
	reminder = re.sub(' +',' ',reminder).strip()
	not_found = len(reminder.split())
	return reminder, not_found, 1 - not_found / (  0.0+len(s.split()) )

@memoize_to_disk
def tuples(dataset_filename):
	n = 0
	with open(dataset_filename) as infile:
		for line in infile:
			n += 1
	return n

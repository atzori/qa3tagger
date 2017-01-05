#
# webserver serving QA3 Question Answering over Data Cube
# from QALD6 task3
#
# python webserver.py
# Running on http://localhost:5000/


# INITIAL SETUP

# turn logging on; setting log format
import logging
logger = logging.getLogger()
logger.handlers = [] # not documented! as per: http://stackoverflow.com/questions/3630774/logging-remove-inspect-modify-handlers-configured-by-fileconfig
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s: %(message)s')
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)

# imports
from qald6.api import datasets_from_dir, Tagger
#from IPython.core.display import HTML
#from IPython.display import display
import sys
SETUP_DONE = True

# BOOTSTRAP LOADING

# get list of datasets
datasets = datasets_from_dir('./benchmarkdatasets')
#		print len(datasets), datasets[:3]

# get list of questions (each one is a dict)
from qald6 import train, measure

test_set = train.read_data(filename='qald-6-test-datacube-questions.json')
questions =  [t['q'] for t in test_set]
#		print len(questions), questions[:3]


# datasets loading
taggers = []
for i, dataset in enumerate(datasets[:50]):
	print '\n*** %d) dataset %s' % (i,dataset)
	taggers.append( Tagger(dataset) )



def compute_res(q):
	from collections import defaultdict
	res = defaultdict(list) # keys are questions, values are list of tagged solutions

	for tagger in taggers: # i.e., for each dataset
		logging.info('begin tagging for %s'% tagger.dataset)
		sys.stdout.write('.'); sys.stdout.flush()
		tagged_q = tagger.tag(q)
		res[q].append ( tagged_q )
		logging.info('end tagging for %s'% tagger.dataset)

	return res # a list of tagged TaggedString


# EVALUATE RES
def evaluate_res(res, question):
	final = {} # keys are questions, values are list of tagdata
	for q in res:
		final[q]=[]
		for tagged_q in res[q]:
			final[q].append(tagged_q.tagdata)


	# final is now computed
	# show evaluation
	print_tag4max = True

	def p(b):
		# return b
		return [x[0] for x in b] # return list of datasets

	print '\n\nFINAL RESULTS'
	results = final[question]
	results = sorted(results, key=lambda e: e[1])
	best = [r for r in results[:10]]
	#print '\n', 'OK' if best3[0][0]==correct_dataset else 'MISTAKE', results[:3]
	if not print_tag4max:
		print '\n\n***',question
		#if best[0][0]==correct_dataset and best[0][1] < best[1][1]-0.8:
		if best[0][1] < best[1][1]-0.8:
			print '\n', 'OK', p(best)
		elif (-best[0][1] + best[1][1])<0.8:
			similar = [c for c in best if (-best[0][1] + c[1])<0.8]
			similar = sorted(similar,key=lambda e: e[2])
			print '\n', 'NOT SURE', len(similar), 
			#if similar[0][2]<similar[1][2] and similar[0][0] ==correct_dataset:
			if similar[0][2]<similar[1][2]:
				print 'OK', 
			elif similar[0][2]==similar[1][2]:
				print 'NOT SURE',
			else:
				print 'MISTAKE',	
			print p(similar)
		else: 
			print '\n', 'MISTAKE', p(best)

	# per Massimo
	res_string = ""
	if print_tag4max:
		print
		chosen_dataset = best[0][0]
		print question
		print chosen_dataset #correct_dataset +'\t'+ chosen_dataset
		for tagged_q in res[question]:
			if tagged_q.tagdata[0] == chosen_dataset:
				#print tagged_q.render(html=False)
				#display(HTML(tagged_q.render(html=True)))
				return {'question': question, 'dataset': chosen_dataset, 'result': tagged_q.render(html=False)}
	return {'msg':'computed'}


def answer(q):
	try:
		logging.info('begin compute_res')
		res = compute_res(q)
		logging.info('begin evaluate_res')
		json_dict = evaluate_res(res, q)
		logging.info('end. done')
		return jsonify( json_dict )
	except:
		import traceback
		err_str = traceback.format_exc()
		logging.error(err_str)
		return jsonify({'msg':'error'})

# MAIN APP

from flask import Flask, request, jsonify
app = Flask(__name__)

#import json

@app.route("/qa3")
def qa3():
	#try:
	question = request.args.get('q', '')
	print 'question: "%s"' % question
	return answer(question)
	#except:
	#	return 'ERROR'

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=8080)
	print qa3()




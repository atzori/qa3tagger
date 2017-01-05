# this file was infact created after LA visit, in April 2016

import logging
from qald6 import tag, measure, train
from qald6.misc import clean_str 

def datasets_from_dir(input_dir):
	""" return a list of nt files from a given directory """
	import os
	return ["%s/%s"%(input_dir,f) for f in os.listdir(input_dir)
		if f.endswith('.nt')]



##########################################
class Tagger:
	"""I'm a tagger, I read an nt file. 
	Then if you give me a question, I tag it."""

	def __init__(self, nt_file):
		self.infile = nt_file
		self.index = None # will be the label_map
		self.__create_index()
		d = nt_file
		if d.endswith('.nt'): 
			d = d[:-3] 
		if '/' in d:
			d = d[d.rfind('/')+1:]
		self.dataset = d 

	def __create_index(self):
		"""create an in-memory index of labels """
		task = "creating index for %s" % self.infile 
		logging.info("begin %s"%task)
		self.index = tag.labels_map(self.infile,fast=True)
		logging.info("end %s"%task)

	def tag(self, text):
		dataset = self.dataset
		dl = train.dataset_labels() # extra dataset labels

		preprocessed_question , tokens = clean_str(text)
		found_labels = tag.find_matching_labels(preprocessed_question,self.index,presorted=True)

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

		tagdata = tuple([
			dataset, 
			len(words_missing2)-wordup*1.1,
			len(words_missing),
			' '.join(words_missing2), 
			' '.join(words_missing3)])

		question = TaggedString(text,preprocessed_question,found_labels,self.index,tagdata)
		
		return question

	def __str__(self):
		return "Tagger for %s (file: %s)" % (self.dataset, self.infile)


##########################################
class TaggedString:
	"""a question. Similar to a string but internally taggable and stemmable"""

	def __init__(self, question,preprocessed_question,found_labels,labels_map,tagdata):
		if not isinstance(question,basestring): 
			raise ValueError('a question must be a str')
		self.text = question
		self.preprocessed_question = preprocessed_question
		self.found_labels = found_labels
		self.labels_map = labels_map
		self.tagdata = tagdata

	def render(self,html=False):
		question = self.text
		try:
			return tag.render(self.text,
				self.preprocessed_question,
				self.found_labels,
				self.labels_map,
				html=html)
		except:
			return 'NOT ABLE TO RENDER'


	def __str__(self):
		return 'TaggedString "%s"' % self.text



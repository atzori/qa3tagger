# QA3tagger - A tagger (entity recognition) tool for the Question Answering over Data Cubes (QALD6 Task3)

## Introduction
This repository contains the tagger used by [QA3 (QAcube)](http://qa3.link/), awarded 2nd place at the QALD6 task3 challenge.

## Setup
From main dir, run the following to download dataset dumps:

	wget http://linkedspending.aksw.org/extensions/page/page/export/qbench2datasets.zip
	unzip qbench2datasets.zip 
	#optionally: rm qbench2datasets.zip

Also run:

	pip install -r requirements.txt
	python -m nltk.downloader stopwords punkt wordnet

## Run

Run `python webserver.py` and go to [http://127.0.0.1:8080/qa3?q=How much was spent in Nigeria?](http://127.0.0.1:8080/qa3?q=How much was spent in Nigeria?). It depends on python Flesk.

You can also use Docker:

	# may take more than minutes (!) and produces a large (5Gb) image
	# this is mainly due to download of qbench2datasets and index creation
	time docker build -t atzori/qa3tagger .
	#or: time docker build -t atzori/qa3tagger https://bitbucket.org/atzori/qa3tagger.git
	

	# run container
	docker run -p 8080:8080 --name qa3tagger atzori/qa3tagger


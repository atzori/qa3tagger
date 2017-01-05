FROM python:2.7-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app

# download file and reduce files at the end

# "python -c" elaborates datasets and cache results in ./memoize_to_disk/*.pkl
# without running the main app

#RUN apt-get update && apt-get install -y unzip wget && \
RUN	wget -O qbench2datasets.zip "http://linkedspending.aksw.org/extensions/page/page/export/qbench2datasets.zip" && \
	unzip qbench2datasets.zip && \
	rm qbench2datasets.zip && \
	pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader stopwords punkt wordnet && \
	python -c "import webserver" && \
	cd benchmarkdatasets && \
	echo "cleaning dataset to save space" && \
	(for file in *; do cp /dev/null "$file"; done) && \
	cd ..

# alternatively (dangerous because of ls):
# 	(ls -1 | xargs -n1 cp /dev/null) && \

# this will not work properly; files should be keeped and emptied instead, with ls / xargs
# rm -rf benchmarkdatasets/ 

CMD ["python","webserver.py"]

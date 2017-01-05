FROM python:2.7

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app

RUN apt-get update && apt-get install -y unzip wget

RUN	pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader stopwords punkt wordnet

RUN wget -O qbench2datasets.zip "http://linkedspending.aksw.org/extensions/page/page/export/qbench2datasets.zip" && \
	unzip qbench2datasets.zip && \
	rm qbench2datasets.zip

# elaborates datasets and cache results in ./memoize_to_disk/*.pkl
# without running the main app
RUN python -c "import webserver"

RUN rm -rf benchmarkdatasets/

CMD ["python","webserver.py"]

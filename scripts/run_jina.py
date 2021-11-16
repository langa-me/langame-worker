import numpy as np
from jina import DocumentArray, Executor, requests, Flow, Document
# from jina.types.document.generators import from_files


from glob import glob
import re

class CharEmbed(Executor):  # a simple character embedding with mean-pooling
    offset = 32  # letter `a`
    dim = 127 - offset + 1  # last pos reserved for `UNK`
    char_embd = np.eye(dim) * 1  # one-hot embedding for all chars

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            r_emb = [ord(c) - self.offset if self.offset <= ord(c) <= 127 else (self.dim - 1) for c in d.text]
            d.embedding = self.char_embd[r_emb, :].mean(axis=0)  # average pooling

class Indexer(Executor):
    _docs = DocumentArray()  # for storing all documents in memory

    @requests(on='/index')
    def foo(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)  # extend stored `docs`

    @requests(on='/search')
    def bar(self, docs: DocumentArray, **kwargs):
        docs.match(self._docs, metric='euclidean', limit=20)


f = (Flow(port_expose=12345, protocol='http', cors=True)
        .add(uses=CharEmbed, replicas=2)
        .add(uses=Indexer))  # build a Flow, with 2 shard CharEmbed, tho unnecessary


with f:
    text = "\n".join([open(f, 'r').read() for f in glob("./data/augment/*.txt")]).split("\n")
    regex = re.compile(r'[^a-zA-Z0-9]')
    nd = []
    for e in text:
        parsed = [e.strip() for e in regex.sub(' ', e).split('     ')]
        nd.append(parsed[0])
    f.post('/index', (Document(text=e) for e in nd))  # index all lines of _this_ file
    f.block()  # block for listening request
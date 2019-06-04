
import xml.sax
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID,DATETIME,NUMERIC
from whoosh.query import *
from whoosh.qparser import QueryParser
from whoosh.analysis import *
import sys
import os


class DataHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        #dati documento corrente
        self.tags = {}
        self.initDict()
        #tag corrente
        self.CurrentTag = ""

    def startElement(self, name, attr):
        self.CurrentTag = name
        if not self.tags.get(name) and name != "dblp":
            self.tags[name] = ""

    def characters(self, content):
        content = content.strip()
        if content != "":
            if self.CurrentTag != "" and self.CurrentTag != "dblp":
                if self.tags[self.CurrentTag] != "":
                        self.tags[self.CurrentTag] += u", " + u(content)
                else:
                    self.tags[self.CurrentTag] = u(content)

    def endElement(self, tag):
        if tag == "article" or tag == "inproceedings" or tag == "proceedings2" or tag == "book" or tag == "incollection" or tag == "phdthesis" or tag == "mastersthesis" or tag == "www" or tag == "person" or tag == "data":
            write_index(self.tags)
            self.tags = {}
            self.initDict()
        self.CurrentTag = ""

    def initDict(self):
        self.tags["author"] = ""
        self.tags["editor"] = ""
        self.tags["title"] = ""
        self.tags["booktitle"] = ""
        self.tags["pages"] = ""
        self.tags["year"] = ""
        self.tags["address"] = ""
        self.tags["journal"] = ""
        self.tags["volume"] = ""
        self.tags["number"] = ""
        self.tags["month"] = ""
        self.tags["url"] = ""
        self.tags["ee"] = ""
        self.tags["cdrom"] = ""
        self.tags["cite"] = ""
        self.tags["publisher"] = ""
        self.tags["note"] = ""
        self.tags["crossref"] = ""
        self.tags["isbn"] = ""
        self.tags["series"] = ""
        self.tags["school"] = ""
        self.tags["chapter"] = ""
        self.tags["publnr"] = ""


def write_index(doc):
    #scrivo il documento nell'indice
    writer.add_document(author=doc["author"], editor=doc["editor"], title=doc["title"], booktitle=doc["booktitle"], pages=doc["pages"], year=doc["year"],
                        address=doc["address"], journal=doc["journal"], volume=doc["volume"], number=doc["number"], month=doc["month"], url=doc["url"],
                        ee=doc["ee"], cdrom=doc["cdrom"], cite=doc["cite"], publisher=doc["publisher"], note=doc["note"], crossref=doc["crossref"],
                        isbn=doc["isbn"], series=doc["series"], school=doc["school"], chapter=doc["chapter"], publnr=doc["publnr"])


def stampaRisultato(results):
    i = 1
    if len(results) == 0:
        print("Nessun risultato!!")
    else:
        for res in results:
            print("-----------------------------------------")
            print(i, ") title: ", res["title"])
            print("author: ", res["author"])
            print("year: ", res["year"])
            i += 1


if not os.path.exists("indexdir"):
    os.mkdir("indexdir")
schema = Schema(author=TEXT(stored=True), editor=TEXT(stored=True), title=TEXT(stored=True, analyzer=StemmingAnalyzer()), booktitle=TEXT(stored=True, analyzer=StemmingAnalyzer()), pages=TEXT(stored=True), year=TEXT(stored=True), address=TEXT(stored=True),
                    journal=TEXT(stored=True, analyzer=StemmingAnalyzer()), volume=TEXT(stored=True), number=TEXT(stored=True), month=TEXT(stored=True), url=TEXT(stored=True), ee=TEXT(stored=True), cdrom=TEXT(stored=True), cite=TEXT(stored=True),
                    publisher=TEXT(stored=True), note=TEXT(stored=True, analyzer=StemmingAnalyzer()), crossref=TEXT(stored=True), isbn=TEXT(stored=True), series=TEXT(stored=True), school=TEXT(stored=True), chapter=TEXT(stored=True, analyzer=StemmingAnalyzer()),
                    publnr=TEXT(stored=True))

ix = create_in("indexdir", schema)
writer = ix.writer()


parser = xml.sax.make_parser()
handler = DataHandler()
parser.setContentHandler(handler)
parser.parse('../test.xml')

writer.commit(optimize=True)
#il searcher va fatto dopo la commit!!
searcher = ix.searcher()
myquery = input("cosa vuoi cercare? ")


parser = QueryParser("author", schema=ix.schema)
query = parser.parse(myquery)
results = searcher.search(query, limit=30)

stampaRisultato(results)
searcher.close()






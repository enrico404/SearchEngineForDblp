import xml.sax
import os
class DataHandler(xml.sax.handler.ContentHandler):
    def __init__(self, ixwriter):
        self.id = 0
        #dati documento corrente
        self.tags = {}
        self.initDict()
        #tag corrente
        self.CurrentTag = ""
        self.writer = ixwriter

    def startElement(self, name, attr):
        self.CurrentTag = name
        if not self.tags.get(name) and name != "dblp":
            self.tags[name] = ""

    def characters(self, content):
        content = content.strip()
        if content != "":
            if self.CurrentTag != "" and self.CurrentTag != "dblp":
                if self.tags[self.CurrentTag] != "":
                        self.tags[self.CurrentTag] += ", " + content
                else:
                    self.tags[self.CurrentTag] = content

    def endElement(self, tag):
        if tag == "article" or tag == "inproceedings" or tag == "proceedings2" or tag == "book" or tag == "incollection" or tag == "phdthesis" or tag == "mastersthesis" or tag == "www" or tag == "person" or tag == "data":
            self.id += 1
            self.write_index(self.tags, tag, self.id)
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

    def write_index(self,doc, startTag, id):
        #scrivo il documento nell'indice
        self.writer.add_document(key=id, type=startTag, author=doc["author"], editor=doc["editor"], title=doc["title"], booktitle=doc["booktitle"], pages=doc["pages"], year=doc["year"],
                            address=doc["address"], journal=doc["journal"], volume=doc["volume"], number=doc["number"], month=doc["month"], url=doc["url"],
                            ee=doc["ee"], cdrom=doc["cdrom"], cite=doc["cite"], publisher=doc["publisher"], note=doc["note"], crossref=doc["crossref"],
                            isbn=doc["isbn"], series=doc["series"], school=doc["school"], chapter=doc["chapter"], publnr=doc["publnr"])
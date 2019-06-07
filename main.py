import xml.sax
import whoosh.scoring
import whoosh.index
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID,DATETIME,NUMERIC
from whoosh.query import *
from whoosh.qparser import QueryParser
from whoosh.analysis import *
from utils import DataHandler as DH
from utils import QueryManager as QM
import os


def stampaRisultato(results, fields):
    localFields = ["title","link", "author", "year"]
    i = 1
    if len(results) == 0:
        print("Nessun risultato!!")
    else:
        #print di stampare il risultato devo ordinare per score
        results.sort(key= lambda x: x.score, reverse=True)
        for res in results:
            print("-----------------------------------------")
            print(i, ") title: ", res.dic["title"])
            print("type: ", res.dic["type"])
            print("link: ", res.dic["ee"])
            print("author: ", res.dic["author"])

            print("year: ", res.dic["year"])
            print("score: ", res.score)
            i += 1
            for field in fields:
                if field in localFields:
                    continue
                else:
                    print(field+": ", res.dic[field])


class Hit:
    def __init__(self, hits):
        self.dic = {}
        self.transform(hits)
        self.score = hits.score

    def transform(self, hits):
        for key, val in hits.items():
            self.dic[key] = val



def element_filter(results, type):
    filtered_list = []
    if type != "":
        for res in results:
            if res.dic["type"] == type:
                filtered_list.append(res)
        return filtered_list
    return results

if __name__ == "__main__":


    #ID considera il valore per la sua interezza, ideale per url.
    #i field che supportano le phrasal queries sono quelli con phrase=true
    schema = Schema(key=TEXT(stored=True), type=TEXT(stored=True), author=TEXT(stored=True, phrase=True),
                    title=TEXT(stored=True, phrase=True), year=TEXT(stored=True),
                    journal=TEXT(stored=True, phrase=True), ee=ID(stored=True), publisher=TEXT(stored=True))

    # schema = Schema(key=NUMERIC(stored=True), type=TEXT(stored=True), author=TEXT(stored=True, phrase=True),
    #                 editor=TEXT(stored=True),
    #                 title=TEXT(stored=True, phrase=True),
    #                 booktitle=TEXT(stored=True, phrase=True), pages=TEXT(stored=True),
    #                 year=TEXT(stored=True), address=TEXT,
    #                 journal=TEXT(stored=True, phrase=True), volume=TEXT,
    #                 number=TEXT(stored=True), month=TEXT, url=ID(stored=True), ee=ID(stored=True),
    #                 cdrom=TEXT(stored=True), cite=TEXT,
    #                 publisher=TEXT(stored=True), note=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    #                 crossref=TEXT(stored=True), isbn=TEXT, series=TEXT, school=TEXT,
    #                 chapter=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    #                 publnr=TEXT(stored=True))

    # mi serve nel caso in cui non ho fields specificati nella query
    schemaFields = ["type","author","title","year", "journal","ee","publisher"]
    #se l'indice è già costruito non lo devo rifare
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
        ix = create_in("indexdir", schema)
        writer = ix.writer()

        parser = xml.sax.make_parser()
        handler = DH.DataHandler(writer)
        parser.setContentHandler(handler)
        parser.parse('../test.xml')

        writer.commit(optimize=True)
    else:
        ix = whoosh.index.open_dir("indexdir", schema=schema)


    querystring = ""
    type = ""
    while querystring != "0":
        # il searcher va fatto dopo la commit!!
        print()
        print("scegli il modello di ranking: ")
        print("1) BM5F")
        print("2) PL2")
        choice = int(input())
        if choice == 1:
            searcher = ix.searcher(weighting=whoosh.scoring.BM25F)
        else:
            searcher = ix.searcher(weighting=whoosh.scoring.PL2)

        querystring = input("cosa vuoi cercare? (0 per terminare) \n")
        if querystring != "0":
            queryman = QM.QueryManager()
            fields, myquery = queryman.transform(querystring)
            resTmp = []
            results = []
            resSetLocal = set()
            resSetTotal = set()
            newFields = fields
            #var per capire se sto per effettuare una ricerca per tipo (article, proceedings....)
            typesearch = False
            #se i fields non sono specificati o specifico solo il tipo di doc devo cercare tra tutti i field che ho a disposizione
            for field in fields:
                if field not in schemaFields and "." not in field:
                    typesearch = True

            if len(fields) == 0 or typesearch:
                if typesearch:
                    #è possibile specificare un solo tipo di doc
                    type = fields[0]
                    newFields = []
                    fields = []
                for field in schemaFields:
                    #per ogni parola nella lista myquery
                    for q in myquery:
                        qparser = QueryParser(field,schema=ix.schema)
                        #qparser.remove_plugin_class(QueryParser.WildcardPlugin)
                        query = qparser.parse(q)
                        resTmp = searcher.search(query)
                        for res in resTmp:
                            el = Hit(res)
                            resSetTotal.add(el)
            else:
                newFields = []
                # for field in fields:
                #     if "." in field:
                #         tmpQuery = myquery + " " + field.split(".")[0]
                #         fields.append(field.split(".")[0])
                #         fields.remove(field)
                #
                #         if "type" not in fields:
                #             fields.append("type")
                # mparser = MultifieldParser(fields, schema=ix.schema)
                for field in fields:
                    if "." in field:
                        type = field.split(".")[0]
                        if len(field.split(".")) > 0:
                            qparser = QueryParser(field.split(".")[1],schema=ix.schema)
                            newFields.append(field.split(".")[1])

                    else:
                        #caso in cui non specifico il tipo di documento
                        if field not in newFields:
                            newFields.append(field)
                        qparser = QueryParser(field, schema=ix.schema)
                    for q in myquery:
                        query = qparser.parse(q)
                        resTmp = searcher.search(query)
                        if len(resSetTotal) == 0:
                            for res in resTmp:
                                el = Hit(res)
                                resSetTotal.add(el)
                        else:
                            resSetLocal = set()
                            for res in resTmp:
                                el = Hit(res)
                                resSetLocal.add(el)
                        #intersezione degli insiemi
                        if len(resSetTotal) > 0 and len(resSetLocal) > 0:
                            set1 = set(x.dic["key"] for x in resSetTotal)
                            set2 = set(x.dic["key"] for x in resSetLocal)
                            intersection_ids = set1 & set2
                            resSetTotal = set(i for i in resSetLocal if i.dic["key"] in intersection_ids)
            # whoosh presenta un bug nel parser, per le query ad un solo carattere dichiarate come TEXT nello schema
            # il parser restituisce una query nulla invece della query giusta.. es: number: 1 non lo parsa correttamente, invece number: 11 si

            #traduco il set in lista per gestirlo meglio:
            resSet = [i for i in resSetTotal]
            results = element_filter(resSet, type)

            stampaRisultato(results, newFields)
    searcher.close()






import xml.sax
import whoosh.scoring
import whoosh.index
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID,DATETIME,NUMERIC
from whoosh.qparser import QueryParser
from utils import DataHandler as DH
from utils import QueryManager as QM
import os
import multiprocessing

def stampaRisultato(results, runtime):
    i = len(results)
    if len(results) == 0:
        print("Nessun risultato!!")
    else:
        #print di stampare il risultato devo ordinare per score
        results.sort(key=lambda x: x.score)
        if results != None:
            for res in results:
                print("-----------------------------------------")
                print(i, ") title: ", res.dic["title"])
                print("type: ", res.dic["type"])
                print("link: ", res.dic["ee"])
                print("author: ", res.dic["author"])
                print("year: ", res.dic["year"])
                print("score: ", res.score)
                i -= 1
            print("-----------------------------------------------------------------------")
            print("")
            print("Runtime: ", runtime)
        else:
            print("Nessun risultato!!")


class Hit:
    def __init__(self, hits):
        self.dic = {}
        self.transform(hits)
        self.score = hits.score

    def transform(self, hits):
        for key, val in hits.items():
            self.dic[key] = val


def element_filter_old(results, type):
    filtered_list = []
    if len(type) > 0:
        if "venue" in type or "publication" in type:
            if "venue" in type:
                for res in results:
                    # una venue può essere una procedings (conferenza), un book o un journal (rivista), il journal è riconosciuto
                    # se res.dic["journal"] è != "" e quindi esiste il giornale
                    if res.dic["type"] == "proceedings" or res.dic["type"] == "book" or res.dic["journal"] != "":
                        if res not in filtered_list:
                            filtered_list.append(res)
            if "publication" in type:
                for res in results:
                    # una pubblicazione può essere di tipo: article, incollection, inproceedings, phdthesis, mastersthesis
                    if res.dic["type"] == "article" or res.dic["type"] == "incollection" or res.dic["type"] == "inproceedings" or res.dic["type"] == "phdthesis" or res.dic["type"] == "mastersthesis":
                        if res not in filtered_list:
                            filtered_list.append(res)
            return filtered_list
        else:
            for res in results:
                for t in type:
                    if res.dic["type"] == t:
                        filtered_list.append(res)
                return filtered_list
    return results


# funzione che serve per combinare i documenti e non avere documenti doppi con score differenti
# la lista in input è già ordinata
def combine(lista):
    combinedList = []
    # lista di supporto per semplificare la combinazione dei doc
    combinedListKey = []
    for el in lista:
        if el.dic["key"] not in combinedListKey:
            combinedList.append(el)
            combinedListKey.append(el.dic["key"])
    return combinedList


# funzione che controlla se la lista type è di tipo composto
def iscomposed(type):
    typeFields = ["article", "inproceedings","proceedings","book", "incollection", "phdthesis","mastersthesis", "www","person", "data"]
    for t in type:
        if ("publication" in type or "venue" in type) and t in typeFields:
            return True
    return False


def element_filter(results, type):
    filtered_list = []
    if len(type) > 0:
        for res in results:
            if res.dic["type"] in type or "publication" in type or "venue" in type:
                if "publication" in type and "venue" in type:
                    #el sia pub che venue
                    # check venue
                    if res.dic["type"] == "proceedings" or res.dic["type"] == "book" or res.dic["journal"] != "":
                        #check publication
                        if res.dic["type"] == "article" or res.dic["type"] == "incollection" or res.dic["type"] == "inproceedings" or res.dic["type"] == "phdthesis" or res.dic["type"] == "mastersthesis":
                            # se è un tipo composto es: type = ["publication, venue, article]
                            if iscomposed(type):
                                if res.dic["type"] in type:
                                    filtered_list.append(res)
                            #altrimenti posso aggiungerlo tranquillamente
                            else:
                                filtered_list.append(res)

                elif "publication" in type:
                   # check pub
                    if res.dic["type"] == "article" or res.dic["type"] == "incollection" or res.dic["type"] == "inproceedings" or res.dic["type"] == "phdthesis" or res.dic["type"] == "mastersthesis":
                        # check not venue
                        # if not(res.dic["type"] == "proceedings" or res.dic["type"] == "book" or res.dic["journal"] != ""):
                            # se è un tipo composto es: type = ["publication, venue, article]
                        if iscomposed(type):
                            if res.dic["type"] in type:
                                filtered_list.append(res)
                        # altrimenti posso aggiungerlo tranquillamente
                        else:
                            filtered_list.append(res)
                elif "venue" in type:
                    # prendo solo i venue
                    # check venue
                    if res.dic["type"] == "proceedings" or res.dic["type"] == "book" or res.dic["journal"] != "":
                        # check not publication
                        # if not(res.dic["type"] == "article" or res.dic["type"] == "incollection" or res.dic["type"] == "inproceedings" or res.dic["type"] == "phdthesis" or res.dic["type"] == "mastersthesis"):
                            # se è un tipo composto es: type = ["publication, venue, article]
                        if iscomposed(type):
                            if res.dic["type"] in type:
                                filtered_list.append(res)
                        # altrimenti posso aggiungerlo tranquillamente
                        else:
                             filtered_list.append(res)
                # caso in cui dentro alla lista type non ci sia publication e/o venue
                else:
                    # se è un tipo consentito lo aggiungo alla lista
                    for t in type:
                        if res.dic["type"] == t:
                            filtered_list.append(res)
        return filtered_list
    else:
        return results


if __name__ == "__main__":

    # ID considera il valore per la sua interezza, ideale per url.
    # i field che supportano le phrasal queries sono quelli con phrase=true
    schema = Schema(key=NUMERIC(stored=True), type=TEXT(stored=True), author=TEXT(stored=True, phrase=True),
                    title=TEXT(stored=True, phrase=True), year=TEXT(stored=True),
                    journal=TEXT(stored=True, phrase=True), ee=ID(stored=True), publisher=TEXT(stored=True))
    # limitatore dei doc risultanti, più è piccolo, più la query viene risolta velocemente
    resultLimiter = 800000

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
        # get the number of processor
        nproc = multiprocessing.cpu_count()
        writer = ix.writer(procs=nproc, limitmb=512)

        parser = xml.sax.make_parser()
        handler = DH.DataHandler(writer)
        parser.setContentHandler(handler)
        parser.parse('../dblp.xml')

        writer.commit(optimize=True)
    else:
        ix = whoosh.index.open_dir("indexdir", schema=schema)

    # il searcher va fatto dopo la commit!!
    print()
    print("scegli il modello di ranking: ")
    print("1) BM25F")
    print("2) PL2")
    choice = int(input())
    if choice == 1:
        searcher = ix.searcher(weighting=whoosh.scoring.BM25F)
    else:
        searcher = ix.searcher(weighting=whoosh.scoring.PL2)

    querystring = ""
    while querystring != "0":
        querystring = input("cosa vuoi cercare? (0 per terminare) \n")
        if querystring != "0":
            type = []
            queryman = QM.QueryManager()
            fields, myquery = queryman.transform(querystring)
            resTmp = []
            results = []
            resSetLocal = set()
            resSetTotal = set()

            if len(fields) > 0 and len(fields) == len(myquery):
                i = 0
                while i < len(fields):
                    # se è di tipo: publication.title
                    if "." in fields[i]:
                        if fields[i].split(".")[0] not in type and not fields[i].split(".")[0] in schemaFields:
                            type.append(fields[i].split(".")[0])
                        qparser = QueryParser(fields[i].split(".")[1], schema=ix.schema)
                        query = qparser.parse(myquery[i])
                        resTmp = searcher.search(query, limit=resultLimiter)
                        runtime = resTmp.runtime
                        if len(resSetTotal) == 0:
                            for res in resTmp:
                                el = Hit(res)
                                resSetTotal.add(el)
                        else:
                            resSetLocal = set()
                            for res in resTmp:
                                el = Hit(res)
                                resSetLocal.add(el)
                        if len(resSetTotal) > 0 and len(resSetLocal) > 0:
                            set1 = set(x.dic["key"] for x in resSetTotal)
                            set2 = set(x.dic["key"] for x in resSetLocal)
                            intersection_ids = set1 & set2
                            resSetTotal = set(i for i in resSetLocal if i.dic["key"] in intersection_ids)
                        i += 1
                    # se è un field delllo schema (titolo, year..)
                    elif fields[i] in schemaFields:
                            qparser = QueryParser(fields[i], schema=ix.schema)
                            query = qparser.parse(myquery[i])
                            resTmp = searcher.search(query, limit=resultLimiter)
                            runtime = resTmp.runtime
                            if len(resSetTotal) == 0:
                                for res in resTmp:
                                    el = Hit(res)
                                    resSetTotal.add(el)
                            else:
                                resSetLocal = set()
                                for res in resTmp:
                                    el = Hit(res)
                                    resSetLocal.add(el)
                            if len(resSetTotal) > 0 and len(resSetLocal) > 0:
                                set1 = set(x.dic["key"] for x in resSetTotal)
                                set2 = set(x.dic["key"] for x in resSetLocal)
                                intersection_ids = set1 & set2
                                resSetTotal = set(i for i in resSetLocal if i.dic["key"] in intersection_ids)
                            i += 1
                    #se non è un field dello schema es: publication, venue
                    else:
                        try:
                            if fields[i] != "" and not fields[i] in schemaFields:
                                type.append(fields[i])
                        except:
                            pass
                        flag = False
                        tmpFields = []
                        for field in fields:
                            if field.split(".")[0] not in tmpFields:
                                tmpFields.append(field.split(".")[0])

                        if "venue" in tmpFields and "publication" in tmpFields:
                            # effettuo una ricerca su tutti i campi
                            for field in schemaFields:
                                qparser = QueryParser(field, schema=ix.schema)
                                query = qparser.parse(myquery[i])
                                resTmp = searcher.search(query, limit=resultLimiter)
                                runtime = resTmp.runtime
                                if fields[i] == "venue":
                                    if field == "author" or field == "title":
                                        continue
                                if len(resSetTotal) == 0:
                                    for res in resTmp:
                                        el = Hit(res)
                                        resSetTotal.add(el)
                                else:
                                    resSetLocal = set()
                                    for res in resTmp:
                                        el = Hit(res)
                                        resSetLocal.add(el)
                                if len(resSetTotal) > 0 and len(resSetLocal) > 0:
                                    set1 = set(x.dic["key"] for x in resSetTotal)
                                    set2 = set(x.dic["key"] for x in resSetLocal)
                                    intersection_ids = set1 & set2
                                    resSetTotal = set(i for i in resSetLocal if i.dic["key"] in intersection_ids)
                        else:
                            for field in schemaFields:
                                qparser = QueryParser(field, schema=ix.schema)
                                query = qparser.parse(myquery[i])
                                resTmp = searcher.search(query, limit=resultLimiter)
                                runtime = resTmp.runtime
                                for res in resTmp:
                                    el = Hit(res)
                                    resSetTotal.add(el)
                        i += 1
            else:
                if len(fields) == 0:
                    # phrasal search
                    if myquery[0][0] == "\"":
                        for field in schemaFields:
                            qparser = QueryParser(field, schema=ix.schema)
                            query = qparser.parse(myquery[0])
                            resTmp = searcher.search(query, limit=resultLimiter)
                            runtime = resTmp.runtime
                            for res in resTmp:
                                el = Hit(res)
                                resSetTotal.add(el)
                    else:
                        # keyword search
                        for q in myquery[0].split(" "):
                            for field in schemaFields:
                                qparser = QueryParser(field, schema=ix.schema)
                                query = qparser.parse(q)
                                resTmp = searcher.search(query, limit=resultLimiter)
                                runtime = resTmp.runtime
                                for res in resTmp:
                                    el = Hit(res)
                                    resSetTotal.add(el)

                # caso in cui mi manca un campo o più nei fields
                else:
                    for q in myquery:

                        if q[0] != "\"":
                            queryList = q.split(" ")
                            i = 0
                            try:
                                if fields[i] != "":
                                    if fields[i].split(".")[0] not in type and not fields[i].split(".")[0] in schemaFields:
                                        type.append(fields[i].split(".")[0])
                            except:
                                pass

                            while i < len(queryList):
                                #ricerca in tutti i field nel caso in cui non specifico i field
                                for field in schemaFields:
                                    qparser = QueryParser(field, schema=ix.schema)
                                    query = qparser.parse(queryList[i])
                                    resTmp = searcher.search(query, limit=resultLimiter)
                                    runtime = resTmp.runtime
                                    if len(resSetTotal) == 0:
                                        for res in resTmp:
                                            el = Hit(res)
                                            resSetTotal.add(el)
                                    else:
                                        resSetLocal = set()
                                        for res in resTmp:
                                            el = Hit(res)
                                            resSetLocal.add(el)
                                    if len(resSetTotal) > 0 and len(resSetLocal) > 0:
                                        set1 = set(x.dic["key"] for x in resSetTotal)
                                        set2 = set(x.dic["key"] for x in resSetLocal)
                                        intersection_ids = set1 & set2
                                        resSetTotal = set(i for i in resSetLocal if i.dic["key"] in intersection_ids)
                                i += 1
                        else:
                                for field in schemaFields:
                                    qparser = QueryParser(field, schema=ix.schema)
                                    query = qparser.parse(q)
                                    resTmp = searcher.search(query, limit=resultLimiter)
                                    runtime = resTmp.runtime
                                    if len(resSetTotal) == 0:
                                        for res in resTmp:
                                            el = Hit(res)
                                            resSetTotal.add(el)
                                    else:
                                        resSetLocal = set()
                                        for res in resTmp:
                                            el = Hit(res)
                                            resSetLocal.add(el)
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
            finalResults = []
            finalResults = combine(results)
            stampaRisultato(finalResults, runtime)
    searcher.close()






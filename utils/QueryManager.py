
class QueryManager:
    def __init__(self):
        self.fields = []
        self.query = []
        self.element = ""
    def transform(self, querystring):
        for word in querystring.split(" "):
            if word.endswith(":"):
                self.fields.append(word[0:len(word) - 1])
                if self.element != "":
                    self.query.append(self.element)
                    self.element = ""
            else:
                if self.element == "":
                    self.element = word
                else:
                    self.element += " "+word
        #se ho un elemento in sospeso da aggiungere lo metto
        if self.element != "":
            self.query.append(self.element)
            self.element = ""
        return self.fields, self.query
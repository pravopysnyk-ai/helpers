class FormExtractorInflector():
    matchings_part = {"VERB":"VERB", "PRON":"NPRO", "DET":"NPRO","ADJ":"ADJF", "NUM":"NUMR", "NOUN":"NOUN"} #match POS for inflector to be readable

    #cases from movainstitute to inflector
    cases = {"Nom":"N", "Gen": "R", "Dat":"D", "Acc":"Z", "Ins":"O", "Loc":"M", "Voc":"K"}

    v_forms = {"Inf" : ["Inf"], "Pr1": ["Pres", "1"], "Pr2" : ["Pres", "2"],
                    "Pr3" : ["Pres", "3"], "Fu1" : ["Fut", "1"], "Fu2" : ["Fut", "2"],
                    "Fu3" : ["Fut", "3"], "PsMs" : ["Past", "Masc"], "PsFe" : ["Past", "Fem"],
                    "PsNe" : ["Past", "Neut"]}
    genders = {"Masc":"masc", "Fem":"femn", "Neut":"neut"}
    quanitys = {"Plur":"plur", "Sing":"sing"}
    aspects = {"Perf":"perf", "Imp":None}

    v_forms_rev = {" ".join(v): k for k, v in v_forms.items()}

    def __init__(self, inflector):
        self.infl=inflector

    def c(self, a):
        if a is None: return None
        if a in self.genders: return self.genders[a]
        if a in self.quanitys: return self.quanitys[a]
        if a in self.cases: return self.cases[a]
        if a in self.v_forms_rev: return self.v_forms_rev[a]
        if a in self.aspects: return self.aspects[a]
        return a
    def extract_data(self, sentence_anal, index):
        anal = list(zip(*sentence_anal))

        source = anal[0][index]
        part = anal[2][index]
        if part in self.matchings_part:
            part = self.matchings_part[part]
        descr = anal[4][index]
        descr = descr.split("|")

        case = None
        gender = None
        quantity = None
        verbform = None
        tense = None
        person = None
        aspect = None
        mood = None

        for i in descr:
            ir = i.split("=")
            if ir[0]=="Case":
                case = ir[1]
            elif ir[0]=="Gender":
                gender = ir[1]
            elif ir[0]=="Number":
                quantity = ir[1]
            elif ir[0]=="VerbForm":
                verbform = ir[1]
            elif ir[0]=="Tense":
                tense = ir[1]
            elif ir[0]=="Person":
                person = ir[1]
            elif ir[0]=="Aspect":
                aspect = ir[1]
            elif ir[0]=="Mood":
                mood = ir[1]

        if case is not None:
            return self.c(case), part, self.c(gender), self.c(quantity), self.c(aspect), source
        if verbform == "Inf":
            return "Inf", part, self.c(gender), self.c(quantity), self.c(aspect), source
        if tense is not None:
            if person is None and gender is not None:
                return self.c(" ".join([tense, gender])), part, None, None, None, source#c(aspect)
            else:
                if person is None: person ="1"
                return self.c(" ".join([tense, person])), part, self.c(gender), self.c(quantity), self.c(aspect), source
        if mood=="Imp" and verbform=="Fin":
            if person is None: person="1"
            return "Imp"+person,part,self.c(gender),self.c(quantity),self.c(aspect)
        return None, part, None, None, None, source

    def inflect_word_ignore_part(self, word, case, part, gender=None, quantity=None, perf=None):
        try:
            return self.infl.inflect_word(word, case, part, gender=gender, quantity=quantity), True
        except Exception as e:
            print(e)
            for i in self.matchings_part.keys():
                try:
                    #print(word, case, matchings_part[i], gender, quantity,perf)
                    return self.infl.inflect_word(word, case, self.matchings_part[i], gender=gender, quantity=quantity), True
                except Exception as e:
                    print(e)
                    pass
        return word, False

    def word_inflection_goodness_checker(self, word1, word2):
        score=0
        if word1[-1]==word2[-1]:
            score+=100
        if word1[-1]==word2[-1] and word1[-2]==word2[-2]:
            score+=50
        return score

    def inflect_as_in_sentence(self, sentence_anal, index, word):
        case, part, gender, quantity, aspect, source = self.extract_data(sentence_anal, index)
        # print(case, part, gender, quantity, aspect)
        if part == "ADV" or part=="PUNCT" or part == "ADP":
            return word, True
        try:
            if case=="Z":
                inflection1 = self.inflect_word_ignore_part(word, case, part, gender=gender, quantity=quantity, perf=aspect)
                score1 = self.word_inflection_goodness_checker(inflection1[0], source)
                inflection2 = self.inflect_word_ignore_part(word, "N", part, gender=gender, quantity=quantity, perf=aspect)
                score2 = self.word_inflection_goodness_checker(inflection2[0], source)
                if score1>=score2:
                    return inflection1
                else:
                    return inflection2
            if part=="VERB":
                inflection = self.inflect_word_ignore_part(word, case, part, gender=gender, quantity=quantity, perf=aspect)

                score1 = self.word_inflection_goodness_checker(inflection[0][:-1]+"я", source)
                score2 = self.word_inflection_goodness_checker(inflection[0], source)
                if score1>=score2:
                    inflection=(inflection[0][:-1]+"я", inflection[1])
                return inflection
            return self.inflect_word_ignore_part(word, case, part, gender=gender, quantity=quantity, perf=aspect)
        except Exception as e:
            print(e)
            #print("return original word in inflect_as_in_sentence")
            return word, False
        pass

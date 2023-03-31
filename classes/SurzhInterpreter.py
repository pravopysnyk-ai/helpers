from FormExtractorInflector import FormExtractorInflector
from collections import defaultdict

class SurzhInterpreter(FormExtractorInflector):

    def __init__(self, inflector, spacy_udpipe_model):
        super().__init__(inflector=inflector)
        self.SPACY_UDPIPE_MODEL=spacy_udpipe_model
        pairs_path='/content/drive/MyDrive/ukramarly-main/errorifier/errorifier-data/lexical/surzhiks.txt'

        def pairs_analyzer(pairs):
            res=[]
            for i in range(len(pairs)):
                res.append([self.analyze_sentence(pairs[i][0]), self.analyze_sentence(pairs[i][1])])
            return res

        def bye_parentheses(mystring):
            start = mystring.find("(")
            end = mystring.find(")")
            if start != -1 and end != -1:
                return mystring[start+1:end]
            else:
                return mystring

        def clear_spaces(sentence):
            if sentence[0]==" ":
                sentence = sentence[1:]
            if sentence[-1]==" ":
                sentence = sentence[:-1]
            return sentence


        """
        формат суржиків:
        в списку:
            не правильно - правильно
        в коді:
            suzhiks = [
                [правильно, не правильно],
                [правильно, не правильно],
                ...
            ]

        """
        common_errors_path = pairs_path
        surzhiks2 = []
        with open(common_errors_path, encoding = 'utf-8', mode = 'r') as file:
            for line in file:
                    if len(line)==0:
                      continue
                    if line[0]=="#":
                      continue
                    if line[:2]=="\n":
                      continue
                    words = line.split("; ")
                    left = clear_spaces(bye_parentheses(words[0]))
                    right = clear_spaces(bye_parentheses(words[1].replace("\n","")))
                    left_arr=left.split(" ")
                    rights=right.split(",")
                    right_arr=[]
                    for i in rights:
                        right_arr=i.split(" ")
                        if len(left_arr)!=len(right_arr):
                            right_arr=[]
                    if len(right_arr)==0 or len(right_arr)==1: continue

                    # for i in range(len(right_arr)):
                    #     surzhiks2.append([right_arr[i], left_arr[i]])

                    surzhiks2.append([" ".join(right_arr),left])
                    #words[0] - правильна фраза, words[1] - неправильна фраза

            file.close()
        self.pairs_anal=pairs_analyzer(surzhiks2)
        pass

    def analyze_sentence(self, text: str):
        i = 0
        splitted_by_words = []
        for token in self.SPACY_UDPIPE_MODEL(text):
            splitted_by_words.append ([
                token.text, #оригінал
                token.lemma_, # лема
                token.pos_, # частина мови
                token.dep_, # синтаксична роль
                str(token.morph),# морфологічний опис слова
                0 if token.i == (token.head.i) else token.head.i #індекс голови
            ])
            i += 1
        return splitted_by_words

    def smart_n_grams_creator(self,anal):
        smart_n_grams = []
        for i in range(len(anal)):
            anal[i].append(i)
        for n in range(min(len(anal),4)):
            for i in range(len(anal)):
                n_gram = {}
                n_gram[i] = anal[i][5]
                last = i
                for j in range(len(anal)):
                    if j == n-1:
                        break
                    ind = n_gram[last]
                    n_gram[ind] = anal[ind][5]
                    last = ind
                    if n_gram[ind] == ind:
                        break
                n_gram_words = []
                for j in n_gram.keys():
                    n_gram_words.append(anal[j])
                smart_n_grams.append(n_gram_words)
        return smart_n_grams

    def arePermutations(self, arr1, arr2):
        if (len(arr1) != len(arr2)):
            return False
        hM = defaultdict (int)
        for i in range (len(arr1)):
            x = arr1[i]
            hM[x] += 1
        for i in range (len(arr2)):
            x = arr2[i]
            if x not in hM or hM[x] == 0:
                return False
            hM[x] -= 1
        return True
    def smart_n_grams_clearer(self,smart_n_grams_array):
        output = []
        for i in range(len(smart_n_grams_array)):
            for j in range(len(smart_n_grams_array)):
                if i==j:
                    continue
                anal1 = list(zip(*smart_n_grams_array[i]))
                anal2 = list(zip(*smart_n_grams_array[j]))
                if self.arePermutations(anal1[0], anal2[0]):
                    smart_n_grams_array[i] = "TAGGG"

        for i in smart_n_grams_array:
            if i!="TAGGG":
                output.append(i)
        return output

    def equality_checker(self, pair1_anal, pair2_anal, indexes=None):
        anal1 = list(zip(*pair1_anal))
        norm1=anal1[1]
        anal2 = list(zip(*pair2_anal))
        norm2=anal2[1]
        index_relation = {}
        fl = 0
        tf1=0
        tf2=0
        for i in range(len(norm1)):
            if anal1[2][i]!="PUNCT":
                tf1+=1
        for i in range(len(norm2)):
            if anal2[2][i]!="PUNCT":
                tf2+=1
        if tf1!=tf2:
            return False, index_relation
        for i in range(len(norm1)):
            for j in range(len(norm2)):
                if norm1[i]==norm2[j]:
                    if indexes is not None:
                        index_relation[j] = indexes[i]
                    else:
                        index_relation[j] = i
                    fl+=1
                    break
                elif anal1[2][i]=="PUNCT" or anal2[2][j]=="PUNCT":
                    continue
        return fl==tf1, index_relation

    def prepare_subsitution(self,sentence_anal, pair_anals, indexes, keep_if_same=True):
        anal = list(zip(*sentence_anal))
        pair0=list(zip(*(pair_anals[0])))
        pair=list(zip(*(pair_anals[1])))
        pair_inflected = []
        inflected_successfuly = True
        for i in range(min(len(pair[0]), len(pair0[0]))):
            success = False
            if pair0[0][i] == anal[0][indexes[i]] and keep_if_same:
                infl_pair, success = pair[0][i], True
            else:
                infl_pair, success = self.inflect_as_in_sentence(sentence_anal, indexes[i], pair[0][i])
            if not success:
                inflected_successfuly = False
            pair_inflected.append(infl_pair)
        return pair_inflected, inflected_successfuly

    def get_indexes_for_substitution(self,n_grams, pair_anal):
        for i in range(len(n_grams)):
            indexes = {ind : n_grams[i][ind][6] for ind in range(len(n_grams[i]))}
            equality, connection = self.equality_checker(n_grams[i], pair_anal[0], indexes=indexes)
            if equality:
                return True, connection, n_grams[i]
        return False, None, None

    def substitude(self,anal, smart_n_grams, pair_anal,keep_if_same=True):
        sentence_arr=list(list(zip(*anal))[0])
        found, indexes, _ = self.get_indexes_for_substitution(smart_n_grams, pair_anal)
        changed = True
        if not found:
            tokens = ["$KEEP" for i in range(len(sentence_arr))]
        else:
            inflected_pair, inflected_successfuly = self.prepare_subsitution(anal, pair_anal, indexes, keep_if_same=keep_if_same)
            changed = inflected_successfuly
            tokens = ["$KEEP" for i in range(len(sentence_arr))]
            for i in indexes.keys():
                sentence_arr[indexes[i]] = inflected_pair[i]
                tokens[indexes[i]] = "$ANTISURZHIFY"
        return sentence_arr, tokens, changed

    def sentence_adj_changer2(self, sentence):
        anal = self.analyze_sentence(sentence)
        ress = list(zip(*anal))
        result = list(ress[0])
        for i in range(len(ress[0])):
            if ress[2][i]=="NOUN":
                for j in range(len(ress[0])):
                    if ress[2][j]=="ADJ" and ress[5][j]==i:
                        result[j]=self.inflate_word_as_regardless(ress[0][i],ress[0][j])
        return " ".join(result)

    def smart_n_grams_token_clearer(self,n_grams):
        res = []
        for i in n_grams:
            fl=True
            for desc in i:
                if desc[3]!="$ANTISURZHIFY":
                    fl=False
            if fl:
                res.append(i)
        return res

    def antisurzhifier(self, sentence, tokens=None):
        anal = self.analyze_sentence(sentence)
        if tokens is not None:
          for i in range(len(anal)):
              anal[i][3]=tokens[i]
        if tokens is None:
          smart_n_grams = (self.smart_n_grams_clearer(self.smart_n_grams_creator(anal)))
        else:
          smart_n_grams = self.smart_n_grams_token_clearer(self.smart_n_grams_clearer(self.smart_n_grams_creator(anal)))
        pair_anal = self.pairs_anal[0]
        res=self.substitude(anal, smart_n_grams, pair_anal[::-1], keep_if_same=True)
        sentence_res = res[0]
        for pair_anal in self.pairs_anal:
            if sentence_res!=list(list(zip(*anal))[0]):
                anal = self.analyze_sentence(" ".join(sentence_res))
            if tokens is None:
              smart_n_grams = (self.smart_n_grams_clearer(self.smart_n_grams_creator(anal)))
            else:
              for i in range(len(anal)):
                  anal[i][3]=tokens[i]
              smart_n_grams = self.smart_n_grams_token_clearer(self.smart_n_grams_clearer(self.smart_n_grams_creator(anal)))
            res=self.substitude(anal, smart_n_grams, pair_anal[::-1], keep_if_same=True)
            sentence_res=res[0]
        result=""
        for i in sentence_res:
            puncts=[',','.',':',";",'-']
            if i in puncts:
                result+=i
            else:
                result+=" "+i
        return result[1:]

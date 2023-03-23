import json
import re
import subprocess
import tempfile
import stanza
from symspellpy import SymSpell, Verbosity

class SymSpellUkr:
    def __init__(self, sym_spell, bigrams_path, new_freq_path, dict_path, space_handler, SPACY_UDPIPE_MODEL):
        self.sym_spell = sym_spell
        self.sym_spell.load_bigram_dictionary(bigrams_path, term_index=0, count_index=2, encoding = "utf-8")
        self.sym_spell.load_dictionary(new_freq_path, 0, 1,  encoding = "utf-8")
        self.SPACY_UDPIPE_MODEL = SPACY_UDPIPE_MODEL
        self.pattern = r'"[^"]*"|\d+|[^\u0400-\u04FF]|(\b[А-ЯІЇЄ][А-Яа-яіїєІЇЄ]*\b)'  # ігнорує слова в лапках, некирилицю та слова з великої літери
        self.ukrainian_dict = self.init_dict(dict_path)
        self.space_handler = space_handler

    def init_dict(self, dict_path): # dict always .json
      with open(dict_path, encoding="utf-8") as json_file:
              ukrainian_dict = json.load(json_file)
      ukrainian_dict = set(ukrainian_dict)

      return ukrainian_dict

    def tokenize(self, text):
      if not hasattr(self.tokenize, "nlp"):
          local_tokenizer = stanza.Pipeline(lang="uk", processors="tokenize")
      nlp = local_tokenizer

      tokenized = " ".join([t.text for t in nlp(text).iter_tokens()])
      return tokenized

    def lookup(self, phrase: str):
        # lookup suggestions for multi-word input strings (supports compound
        # splitting & merging)
        verbosity = Verbosity.CLOSEST
        # max edit distance per lookup (per single word, not per whole input string)
        suggestions = self.sym_spell.lookup(
            # regex to ignore (1) words in quotes (2) numbers (3) non-Cyrillic
            phrase, verbosity, max_edit_distance=2, include_unknown=True, ignore_token=self.pattern,
            transfer_casing=True
        )
        # display suggestion term, edit distance, and term frequency
        res = {}
        for s in suggestions:
            res[s.term] = s.count
        return res

    def lookup_compound(self, phrase: str):
        suggestions = self.sym_spell.lookup_compound(
            phrase, max_edit_distance=2, transfer_casing=True
        )
        # display suggestion term, edit distance, and term frequency
        res = {}
        for s in suggestions:
            res[s.term] = s.count
        return res

    def save_capitalization(self, input: str, output: str):
        if input.istitle():
            return output.capitalize()
        if input.isupper():
            return output.upper()
        return output

    def suggest_sentence(self, sent: str):
        pattern = re.compile(self.pattern)
        #sent = self.s_handler.space_oddity(sent)
        sent = sent.split()
        res = {}
        #print(sent)
        for i in range(len(sent)):
            origin = sent[i]
            st = set(origin)
            checked = True
            for c in '";,:.!-_?':
              if c in st:
                checked = False

            if not checked:
              res[i] = {self.save_capitalization(origin, sent[i]): 1}
              continue

            if pattern.match(sent[i]):
                res[i] = {self.save_capitalization(origin, sent[i]): 1}

            else:
                res[i] = self.lookup(sent[i])
                # якщо не реагує, то перевірити ще на злиття
                if sent[i] not in res[i].keys():
                    res[i].update(self.lookup_compound(sent[i]))

        return res, sent

    def correct_sentence(self, sent):
        res = self.suggest_sentence(sent)
        words = []
        for value in res.values():
            words.append([c for c in value.keys()][0])
        return " ".join(words)

    def de_symspell(self, sent):
      if sent in self.ukrainian_dict or len(sent) <= 2 :
        return [sent]
      sym_spell_suggestions, sent = self.suggest_sentence(sent)

      final = []
      for i in range(len(sym_spell_suggestions)):
        my_dict = sym_spell_suggestions[i]
        the_best = [ [key, value] for key, value in my_dict.items() if value == max(my_dict.values())]
        final.append(the_best[0][0] if the_best[0][1] > 0 else sent[i])

      return final


    def spellify(self, sent):
      sent = self.tokenize(sent)
      try:
        splitted = sent.split()
        res = []
        for sp in splitted:
          x = self.de_symspell(sp)[0]
          res.append(x)

        return space_handler.fried_nails(" ".join(res))

      except Exception as ex:
        print("Exception = ", ex)
        return sent

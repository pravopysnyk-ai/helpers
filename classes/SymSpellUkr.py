import json
import re
import subprocess
import tempfile
import stanza
from symspellpy import SymSpell, Verbosity


class SymSpell_Ukr:
    def __init__(self, sym_spell, bigrams_folder_path, new_freq_path, SPACY_UDPIPE_MODEL):
        self.sym_spell = sym_spell
        self.concatenate_files(bigrams_folder_path)
        self.sym_spell.load_bigram_dictionary('concatenated_bigrams.txt', term_index=0, count_index=2, encoding="utf-8")
        self.sym_spell.load_dictionary(new_freq_path, 0, 1, encoding="utf-8")
        self.SPACY_UDPIPE_MODEL = SPACY_UDPIPE_MODEL
        self.pattern = r'"[^"]*"|\d+|[^\u0400-\u04FF]|(\b[А-ЯІЇЄ][А-Яа-яіїєІЇЄ]*\b)'  # ігнорує слова в лапках, некирилицю та слова з великої літери

    def concatenate_files(self, bigrams_folder_path, number_of_files=61):
        data = ""
        from string import ascii_lowercase
        bigrams_paths = [bigrams_folder_path + "/bigrams_part_" + letter1 + letter2 for letter1 in ascii_lowercase for
                         letter2 in ascii_lowercase][:number_of_files]

        for bigrams_path in bigrams_paths:
            with open(bigrams_path, "r", encoding="utf-8") as infile:
                x = infile.read()
                data += x
                data += "\n"

        with open('concatenated_bigrams.txt', 'w', encoding="utf-8") as res:
            res.write(data)
        return

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
        # sent = self.s_handler.space_oddity(sent)
        sent = sent.split()
        res = {}
        # print(sent)
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

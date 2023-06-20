class GrammarInterpreter(object):
  def __init__(self, space_handler, inflector):
    self.space_handler = space_handler
    self.inflector = inflector

  "Grammar intepreter: takes in list of labels and list of words, returns final sentence"
  def __call__(self, words, tags):
    final_sentence = ''
    for i in range(len(words)): #skip start token alltogether for grammar
      if words[i] == '$START':
        word = ''
      else:
        word = words[i]
      if tags[i] == '$KEEP':
        final = word
      if tags[i].startswith('$TRANSFORM'):
        try: #try to use the inflector on the word. usually throws error for OOV
            final = self.reverse_trans(word, tags[i])
        except: #default to keep if can't conjugate
            print("OOV error!")
            final = word
      if tags[i].startswith('$APPEND'):
        final = word + ' ' + tags[i][8:]
      # replacing the erroneous word with the correct one
      if tags[i].startswith('$REPLACE'):
        final = tags[i][9:]
      if tags[i].startswith('$DELETE'):
        final = tags[i][9:]
      final_sentence += f' {final}'

    final_sentence = self.space_handler.space_stripper(final_sentence)
    final_sentence = self.space_handler.fried_nails(final_sentence)
    final_sentence = final_sentence[:1].capitalize() + final_sentence[1:] # making the first letter uppercase
    return final_sentence

  #перетворити слово в нормальне назад суто за тегом
  #наприклад, (прийшла TRANSFORM_VERB_PsMs) -> прийшов
  def reverse_trans(self, word, tag):
    w = self.inflector.helpers(word, tag) #фіксимо слово, щоб його можна було провідміняти (будинка -> будинку)
    descr = tag.split("_")
    pos = descr[1]
    return self.inflector.inflect_word(w, descr[2], pos)

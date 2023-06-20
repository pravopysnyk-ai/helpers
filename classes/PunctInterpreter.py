class PunctInterpreter(object):
  # Takes in words, tags prodced by a punct_anti_tokenizer, outputs sentence
  def __init__(self, space_handler):
    self.space_handler = space_handler

  # Punct intepreter: takes in list of labels and list of words, returns final sentence
  def __call__(self, words, tags):
    final_sentence = ''
    for i in range(len(words)-1): #skip start token alltogether for gramma
      i = i+1
      if tags[i] == '$KEEP':
        final = words[i]
      elif tags[i].startswith('$APPEND'):
        final = words[i] + tags[i][8:]
      elif tags[i].startswith('$REPLACE'):
        final = tags[i][9:]
      elif tags[i] == '$DELETE':
        final = ''
      final_sentence += f' {final}'

    final_sentence = self.space_handler.space_stripper(final_sentence)
    final_sentence = self.space_handler.fried_nails(final_sentence)
    return final_sentence

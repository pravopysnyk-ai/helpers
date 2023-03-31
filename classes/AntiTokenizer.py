import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

class AntiTokenizer(object):
  """
  On creation takes in model name and checkpoint
  main function anti_tokenize, takes in sentence, outputs list of tokens and tags
  will have a separate instance of this class for each model
  """
  def __init__(self, model_name, checkpoint, model_type, space_handler):
    self.space_handler = space_handler
    self.model_type = model_type
    self.tokenizer = AutoTokenizer.from_pretrained(f"/content/drive/MyDrive/model-directories/{model_name}/{checkpoint}")
    self.model = AutoModelForTokenClassification.from_pretrained(f"/content/drive/MyDrive/model-directories/{model_name}/{checkpoint}")
    self.label_decoding = {}
    with open(f"/content/drive/MyDrive/model-directories/{model_name}/label_encoding.txt", 'r') as f:
      lines = [line[:-1] for line in f.readlines()]
    for line in lines:
      label = line.split(' ')[0]
      idx = line.split(' ')[1]
      self.label_decoding[idx] = label

  def __call__(self, orig_sentence):
  # Takes in original sentence, runs predit on it, returns list of words and list of tags
    sentence = '$START ' + self.space_handler.space_oddity(orig_sentence)
    words = sentence.split(' ')
    tokens = self.tokenizer(sentence)
    wordpieces = self.tokenizer.batch_decode(tokens['input_ids'])

    start_or_not_mask = []
    for wordpiece in wordpieces:
      if wordpiece.startswith(' ') or wordpiece in self.space_handler.upr:
        start_or_not_mask.append(1)
      else:
        start_or_not_mask.append(0)

    prediction = self.model.forward(input_ids=torch.tensor(tokens['input_ids']).unsqueeze(0), attention_mask=torch.tensor(tokens['attention_mask']).unsqueeze(0))
    prediction = torch.argmax(prediction.logits.squeeze(), axis=1)
    prediction = [self.label_decoding[str(int(i))] for i in prediction]

    final_tags = []
    for i in range(len(prediction)):
      if start_or_not_mask[i]:
        final_tags.append(prediction[i])
      else:
        pass

    # CHECK/ASSERT LENGTH
    assert len(words) == len(final_tags)
    return words, final_tags

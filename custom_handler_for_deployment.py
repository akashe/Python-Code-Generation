import json

from ts.torch_handler.base_handler import BaseHandler
from model import Seq2Seq
import spacy
import torch
import pickle
import re
import os
import logging

spacy_en = spacy.load('en_core_web_sm')
logger = logging.getLogger(__name__)

'''
One can use a simple module entry itself as mentioned in 
https://pytorch.org/serve/custom_service.html
but we will try a class entry because we have a lot to do
in preprocess and postprocess.
'''


class ModelHandler(BaseHandler):

    def __init__(self):
        self._context = None
        self.initialized = False
        self.explain = False
        self.target = 0

    def initialize(self, context):
        # this func is called while scaling up or increasing the numbers of workers
        self.manifest = context.manifest

        source_file = self.manifest['model']['modelFile']
        properties = context.system_properties
        model_dir = properties.get("model_dir")
        self.device = torch.device("cuda:" + str(properties.get("gpu_id")) if torch.cuda.is_available() else "cpu")

        # Read model serialize/pt file
        serialized_file = self.manifest['model']['serializedFile']
        model_pt_path = os.path.join(model_dir, serialized_file)
        if not os.path.isfile(model_pt_path):
            raise RuntimeError("Missing the model.pt file")

        self.model = torch.jit.load(model_pt_path,map_location=torch.device('cpu'))
        self.model.to(self.device)

        # self.model =

        self.initialized = True

        with open("SRC_stio_local", "rb") as f:
            self.stoi = pickle.load(f)
        with open("TRG_itos_local", "rb") as f:
            self.itos = pickle.load(f)

        self.trg_stoi = {j: i for i, j in enumerate(self.itos)}

        self.answer_max_len = 100

        self.src_pad_idx = self.stoi['<pad>']
        self.trg_pad_idx = self.trg_stoi['<pad>']

    def handle(self, data, context):
        # this function is used during inference
        # Refer https://github.com/pytorch/serve/blob/master/examples/Huggingface_Transformers/Transformer_handler_generalized.py
        # for multiple requests

        # TODO: make it for a batch of requests

        input_text = data[0].get("data")
        if input_text is None:
            input_text = data[0].get("body")
        if isinstance(input_text, (bytes, bytearray)):
            input_text = input_text.decode('utf-8')

        src = self.tokenize(input_text, self.stoi)
        # trg = '<sos>'
        # trg_indexes = [self.stoi[trg]]
        #
        #
        # decoder_outputs = []
        # for i in range(self.answer_max_len):
        #     # TODO: I know this is way to expensive by recalculating encoder attentions
        #     # but with the current implementation getting model.encoder or model.decoder
        #     # is not working
        #     trg_tensor = torch.LongTensor(trg_indexes).unsqueeze(0).to(self.device)
        #     decoder_output, _ = self.model.forward(src, trg_tensor)
        #     pred_token = decoder_output.argmax(2)[:, -1].item()
        #
        #     if pred_token == self.trg_stoi['<eos>']:
        #         break
        #
        #     decoder_outputs.append(self.itos[pred_token])
        #     trg_indexes.append(pred_token)

        src_mask = self.make_src_mask(src)

        enc_src = self.model.encoder.forward(src, src_mask)

        trg = '<sos>'
        trg_indexes = [self.stoi[trg]]

        decoder_outputs = []
        for i in range(self.answer_max_len):
            trg_tensor = torch.LongTensor(trg_indexes).unsqueeze(0).to(self.device)
            trg_mask = self.make_trg_mask(trg_tensor)

            decoder_output, encoder_decoder_attention = self.model.decoder.forward(trg_tensor, enc_src, trg_mask, src_mask)

            pred_token = decoder_output.argmax(2)[:, -1].item()

            if pred_token == self.trg_stoi['<eos>']:
                break
            decoder_outputs.append(self.itos[pred_token])
            trg_indexes.append(pred_token)

        return self.prune_outputs(decoder_outputs)

    def tokenize(self, input, vocab):
        tokenized_input_ = [tok.text.lower() for tok in spacy_en.tokenizer(input)]
        tokenized_input = ['<sos>'] + tokenized_input_ + ['<eos>']

        numericalized_input = [vocab[i] for i in tokenized_input]

        tensor_input = torch.LongTensor([numericalized_input])

        return tensor_input.to(self.device)

    def prune_outputs(self, decoder_outputs):

        def variables_names_in_print(matchobj):
            statement = matchobj.group(1)
            statement = statement.replace(" ", "")
            return "{" + statement + "}"

        decoder_outputs = [i for i in decoder_outputs if
                           i is not '']
        # removing redundant empty token created by tokenizer while identation during tokenization
        combined_output = " ".join(decoder_outputs)
        pruned_output = re.sub(r'\n |\n  |\n   ', r'\n', combined_output)
        # removing empty lines
        pruned_output = re.sub(r'{(.*?)}', variables_names_in_print,
                               pruned_output)
        # setting printing variable names inside print(f'{}') statements

        return [json.dumps(pruned_output)]

    def make_src_mask(self,src):
        src_mask = (src != self.src_pad_idx).unsqueeze(1).unsqueeze(2)

        return src_mask

    def make_trg_mask(self, trg):
        # trg : [batch_size, trg_len]

        # Masking pad values
        trg_pad_mask = (trg != self.trg_pad_idx).unsqueeze(1).unsqueeze(2)
        # trg_pad_mask : [batch_size,1,1, trg_len]

        # Masking future values
        trg_len = trg.shape[1]
        trg_sub_mask = torch.tril(torch.ones((trg_len, trg_len), device=self.device)).bool()
        # trg_sub_mask : [trg_len, trg_len]

        # combine both masks
        trg_mask = trg_pad_mask & trg_sub_mask
        # trg_mask = [batch_size,1,trg_len,trg_len]

        return trg_mask

# -*- coding: utf-8 -*-
"""Conala with original data with python embeddings.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/akashe/Python-Code-Generation/blob/main/Conala_with_original_data_with_python_embeddings.ipynb
"""


import torch
import torch.nn as nn

import math
import time
import pickle
import re

class PositionalEncodingComponent(nn.Module):
  '''
  Class to encode positional information to tokens.
  

  '''
  def __init__(self,hid_dim,device,dropout=0.2,max_len=5000):
    super().__init__()

    assert hid_dim%2==0 # If not, it will result error in allocation to positional_encodings[:,1::2] later

    self.dropout = nn.Dropout(dropout)

    self.positional_encodings = torch.zeros(max_len,hid_dim)

    pos = torch.arange(0,max_len).unsqueeze(1) # pos : [max_len,1]
    div_term  = torch.exp(-torch.arange(0,hid_dim,2)*math.log(10000.0)/hid_dim) # Calculating value of 1/(10000^(2i/hid_dim)) in log space and then exponentiating it
    # div_term: [hid_dim//2]

    self.positional_encodings[:,0::2] = torch.sin(pos*div_term) # pos*div_term [max_len,hid_dim//2]
    self.positional_encodings[:,1::2] = torch.cos(pos*div_term) 

    self.positional_encodings = self.positional_encodings.unsqueeze(0) # To account for batch_size in inputs

    self.device = device

  def forward(self,x):
    x = x + self.positional_encodings[:,:x.size(1)].detach().to(self.device)
    return self.dropout(x)

class FeedForwardComponent(nn.Module):
  '''
  Class for pointwise feed forward connections
  '''
  def __init__(self,hid_dim,pf_dim,dropout):
    super().__init__()

    self.dropout = nn.Dropout(dropout)

    self.fc1 = nn.Linear(hid_dim,pf_dim)
    self.fc2 = nn.Linear(pf_dim,hid_dim)

  def forward(self,x):

    # x : [batch_size,seq_len,hid_dim]
    x = self.dropout(torch.relu(self.fc1(x)))

    # x : [batch_size,seq_len,pf_dim]
    x = self.fc2(x)

    # x : [batch_size,seq_len,hid_dim]
    return x

class MultiHeadedAttentionComponent(nn.Module):
  '''
  Multiheaded attention Component. This implementation also supports mask. 
  The reason for mask that in Decoder, we don't want attention mechanism to get
  important information from future tokens.
  '''
  def __init__(self,hid_dim, n_heads, dropout, device):
    super().__init__()

    assert hid_dim % n_heads == 0 # Since we split hid_dims into n_heads

    self.hid_dim = hid_dim
    self.n_heads = n_heads # no of heads in 'multiheaded' attention
    self.head_dim = hid_dim//n_heads # dims of each head

    # Transformation from source vector to query vector
    self.fc_q = nn.Linear(hid_dim,hid_dim)

    # Transformation from source vector to key vector
    self.fc_k = nn.Linear(hid_dim,hid_dim)

    # Transformation from source vector to value vector
    self.fc_v = nn.Linear(hid_dim,hid_dim)

    self.fc_o = nn.Linear(hid_dim,hid_dim)

    self.dropout = nn.Dropout(dropout)

    # Used in self attention for smoother gradients
    self.scale = torch.sqrt(torch.FloatTensor([self.head_dim])).to(device)

  def forward(self,query,key,value,mask=None):

    #query : [batch_size, query_len, hid_dim]
    #key : [batch_size, key_len, hid_dim]
    #value : [batch_size, value_len, hid_dim]

    batch_size = query.shape[0]

    # Transforming quey,key,values
    Q = self.fc_q(query)
    K = self.fc_k(key)
    V = self.fc_v(value)

    #Q : [batch_size, query_len, hid_dim]
    #K : [batch_size, key_len, hid_dim]
    #V : [batch_size, value_len,hid_dim]

    # Changing shapes to acocmadate n_heads information
    Q = Q.view(batch_size, -1, self.n_heads, self.head_dim).permute(0, 2, 1, 3)
    K = K.view(batch_size, -1, self.n_heads, self.head_dim).permute(0, 2, 1, 3)
    V = V.view(batch_size, -1, self.n_heads, self.head_dim).permute(0, 2, 1, 3)

    #Q : [batch_size, n_heads, query_len, head_dim]
    #K : [batch_size, n_heads, key_len, head_dim]
    #V : [batch_size, n_heads, value_len, head_dim]

    # Calculating alpha
    score = torch.matmul(Q,K.permute(0,1,3,2))/self.scale
    # score : [batch_size, n_heads, query_len, key_len]

    if mask is not None:
      score = score.masked_fill(mask==0,-1e10)

    alpha = torch.softmax(score,dim=-1)
    # alpha : [batch_size, n_heads, query_len, key_len]

    # Get the final self-attention  vector
    x = torch.matmul(self.dropout(alpha),V)
    # x : [batch_size, n_heads, query_len, head_dim]

    # Reshaping self attention vector to concatenate
    x = x.permute(0,2,1,3).contiguous()
    # x : [batch_size, query_len, n_heads, head_dim]

    x = x.view(batch_size,-1,self.hid_dim)
    # x: [batch_size, query_len, hid_dim]

    # Transforming concatenated outputs 
    x = self.fc_o(x)
    #x : [batch_size, query_len, hid_dim] 

    return x, alpha

class EncoderLayer(nn.Module):  
  '''
  Operations of a single layer in an Encoder. An Encoder employs multiple such layers. Each layer contains:
  1) multihead attention, folllowed by
  2) LayerNorm of addition of multihead attention output and input to the layer, followed by
  3) FeedForward connections, followed by
  4) LayerNorm of addition of FeedForward outputs and output of previous layerNorm.
  '''
  def __init__(self, hid_dim,n_heads,pf_dim,dropout,device):
    super().__init__()
    
    self.self_attn_layer_norm = nn. LayerNorm(hid_dim) #Layer norm after self-attention
    self.ff_layer_norm = nn.LayerNorm(hid_dim) # Layer norm after FeedForward component

    self.self_attention = MultiHeadedAttentionComponent(hid_dim,n_heads,dropout,device)
    self.feed_forward = FeedForwardComponent(hid_dim,pf_dim,dropout)

    self.dropout = nn.Dropout(dropout)
    
  def forward(self,src,src_mask):
    
    # src : [batch_size, src_len, hid_dim]
    # src_mask : [batch_size, 1, 1, src_len]

    # get self-attention
    _src, _ = self.self_attention(src,src,src,src_mask)

    # LayerNorm after dropout
    src = self.self_attn_layer_norm(src + self.dropout(_src))
    # src : [batch_size, src_len, hid_dim]

    # FeedForward
    _src = self.feed_forward(src)

    # layerNorm after dropout
    src = self.ff_layer_norm(src + self.dropout(_src))
    # src: [batch_size, src_len, hid_dim]

    return src

class DecoderLayer(nn.Module):
  '''
  Operations of a single layer in an Decoder. An Decoder employs multiple such layers. Each layer contains:
  1) masked decoder self attention, followed by
  2) LayerNorm of addition of previous attention output and input to the layer,, followed by
  3) encoder self attention, followed by
  4) LayerNorm of addition of result of encoder self attention and its input, followed by
  5) FeedForward connections, followed by
  6) LayerNorm of addition of Feedforward results and its input.
  '''
  def __init__(self,hid_dim,n_heads,pf_dim,dropout,device):
    super().__init__()

    self.self_attn_layer_norm = nn.LayerNorm(hid_dim)
    self.enc_attn_layer_norm = nn.LayerNorm(hid_dim)
    self.ff_layer_norm = nn.LayerNorm(hid_dim)

    # decoder self attention
    self.self_attention = MultiHeadedAttentionComponent(hid_dim,n_heads,dropout,device)

    # encoder attention
    self.encoder_attention = MultiHeadedAttentionComponent(hid_dim,n_heads,dropout,device)

    # FeedForward
    self.feed_forward = FeedForwardComponent(hid_dim,pf_dim,dropout)

    self.dropout = nn.Dropout(dropout)

  def forward(self,trg, enc_src,trg_mask,src_mask):

    #trg : [batch_size, trg_len, hid_dim]
    #enc_src : [batch_size, src_len, hid_dim]
    #trg_mask : [batch_size, 1, trg_len, trg_len]
    #src_mask : [batch_size, 1, 1, src_len]

    '''
    Decoder self-attention
    trg_mask is to force decoder to look only into past tokens and not get information from future tokens.
    Since we apply mask before doing softmax, the final self attention vector gets no information from future tokens.
    '''
    _trg, _ = self.self_attention(trg,trg,trg,trg_mask)

    # LayerNorm and dropout with resdiual connection
    trg = self.self_attn_layer_norm(trg + self.dropout(_trg))
    # trg : [batch_size, trg_len, hid_dim]

    '''
    Encoder attention:
    Query: trg
    key: enc_src
    Value : enc_src
    Why? 
    the idea here is to extract information from encoder outputs. So we use decoder self-attention as a query to find important values from enc_src
    and that is why we use src_mask, to avoid getting information from enc_src positions where it is equal to pad-id
    After we get necessary infromation from encoder outputs we add them back to decoder self-attention.
    '''
    _trg, encoder_attn_alpha = self.encoder_attention(trg,enc_src,enc_src,src_mask)

        # LayerNorm , residual connection and dropout
    trg = self.enc_attn_layer_norm(trg + self.dropout(_trg))
    # trg : [ batch_size, trg_len, hid_dim]

    # Feed Forward
    _trg = self.feed_forward(trg)

    # LayerNorm, residual connection and dropout
    trg = self.ff_layer_norm(trg + self.dropout(_trg))

    return trg, encoder_attn_alpha

class Encoder(nn.Module):
  '''
  An encoder, creates token embeddings and position embeddings and passes them through multiple encoder layers
  '''
  def __init__(self,input_dim,hid_dim,n_layers,n_heads,pf_dim,dropout,device,max_length = 5000):
    super().__init__()
    self.device = device

    self.tok_embedding = nn.Embedding(input_dim,hid_dim)
    self.pos_embedding = PositionalEncodingComponent(hid_dim,device,dropout,max_length)

    # encoder layers
    self.layers = nn.ModuleList([EncoderLayer(hid_dim,n_heads,pf_dim,dropout,device) for _ in range(n_layers)])

    self.dropout = nn.Dropout(dropout)

    self.scale = torch.sqrt(torch.FloatTensor([hid_dim])).to(device)

  def forward(self,src,src_mask):

    # src : [batch_size, src_len]
    # src_mask : [batch_size,1,1,src_len]

    batch_size = src.shape[0]
    src_len = src.shape[1]

    tok_embeddings = self.tok_embedding(src)*self.scale

    # token plus position embeddings
    src  = self.pos_embedding(tok_embeddings)

    for layer in self.layers:
      src = layer(src,src_mask)
    # src : [batch_size, src_len, hid_dim]

    return src

class Decoder(nn.Module):
  '''
  An decoder, creates token embeddings and position embeddings and passes them through multiple decoder layers
  '''
  def __init__(self,output_dim,hid_dim,n_layers,n_heads,pf_dim,dropout,device,max_length= 5000):
    super().__init__()

    self.device = device

    self.tok_embedding = nn.Embedding(output_dim,hid_dim)
    self.pos_embedding = PositionalEncodingComponent(hid_dim,device,dropout,max_length)

    # decoder layers
    self.layers = nn.ModuleList([DecoderLayer(hid_dim,n_heads,pf_dim,dropout,device) for _ in range(n_layers)])

    # convert decoder outputs to real outputs
    self.fc_out = nn.Linear(hid_dim,output_dim)

    self.dropout = nn.Dropout(dropout)

    self.scale = torch.sqrt(torch.FloatTensor([hid_dim])).to(device)

  def forward(self, trg, enc_src,trg_mask,src_mask):
    
    #trg : [batch_size, trg_len]
    #enc_src : [batch_size, src_len, hid_dim]
    #trg_mask : [batch_size, 1, trg_len, trg_len]
    #src_mask : [batch_size, 1, 1, src_len]

    batch_size = trg.shape[0]
    trg_len = trg.shape[1]

    tok_embeddings = self.tok_embedding(trg)*self.scale

    # token plus pos embeddings
    trg = self.pos_embedding(tok_embeddings)
    # trg : [batch_size, trg_len, hid_dim]

    # Pass trg thorugh decoder layers
    for layer in self.layers:
      trg, encoder_attention = layer(trg,enc_src,trg_mask,src_mask)
    
    # trg : [batch_size,trg_len,hid_dim]
    # encoder_attention :  [batch_size, n_head,trg_len, src_len]

    # Convert to outputs
    output = self.fc_out(trg)
    # output : [batch_size, trg_len, output_dim]
    
    return output, encoder_attention

class Seq2Seq(nn.Module):
  def __init__(self, encoder, decoder, src_pad_idx, trg_pad_idx, device):
    super().__init__()
    self.encoder = encoder
    self.decoder = decoder
    self.src_pad_idx = src_pad_idx
    self.trg_pad_idx = trg_pad_idx
    self.device = device

  def make_src_mask(self,src):
    # src : [batch_size, src_len]

    # Masking pad values
    src_mask = (src != self.src_pad_idx).unsqueeze(1).unsqueeze(2)
    # src_mask : [batch_size,1,1,src_len]

    return src_mask

  def make_trg_mask(self,trg):
    # trg : [batch_size, trg_len]

    # Masking pad values
    trg_pad_mask = (trg != self.trg_pad_idx).unsqueeze(1).unsqueeze(2)
    # trg_pad_mask : [batch_size,1,1, trg_len]

    # Masking future values
    trg_len = trg.shape[1]
    trg_sub_mask = torch.tril(torch.ones((trg_len,trg_len),device= self.device)).bool()
    # trg_sub_mask : [trg_len, trg_len]

    # combine both masks
    trg_mask = trg_pad_mask & trg_sub_mask
    # trg_mask = [batch_size,1,trg_len,trg_len]

    return trg_mask

  def forward(self,src,trg):

    # src : [batch_size, src_len]
    # trg : [batch_size, trg_len]

    src_mask = self.make_src_mask(src)
    trg_mask = self.make_trg_mask(trg)

    # src_mask : [ batch_size, 1,1,src_len]
    # trg_mask : [batch_size, 1, trg_len, trg_len]

    enc_src = self.encoder(src,src_mask)
    #enc_src : [batch_size, src_len, hid_dim]

    output, encoder_decoder_attention = self.decoder(trg,enc_src,trg_mask,src_mask)
    # output : [batch_size, trg_len, output_dim]
    # encoder_decoder_attention : [batch_size, n_heads, trg_len, src_len]

    return output, encoder_decoder_attention


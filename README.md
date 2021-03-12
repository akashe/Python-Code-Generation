# Python Code Generation

Steps taken for data cleaning
 1. Remove all comments \# and '''...''': This is to reduce the vocab size and make the problem simpler for the model
 2. Replace tabs with "    ": This helps to keep same indentation scheme in the file. Specially for cases with indentation scheme as 4-3-2 spaces.
 3. Replacing multiple line declarations of variables: We use python's own [tokenizer](https://docs.python.org/3/library/tokenize.html). It was creating problems with multiline declarations.  
  

Steps for data processing:
1. Removing duplicate question answer pairs: Original data had many duplicate questions and python codes submitted by as same assignment by different team members. After removing duplicate pairs, the total unique question answer pair we about 3100 as compared to 4600+ original pairs.
2. Tokenization: As said earlier, we used python's own tokenizer. There was a problem with it though. It took strings like the ones present in print('Akash Kumar') as a seperate string token 'Akash Kumar'. This unnecessarily increase vocab size. So tokenized these strings as characters to increase models verstality.
3. formatting with proper indentation: Data had multiple indentation schemes. We identify the indent required and finally replace it with corresponding '\t' to keep sequence length smaller.

Loss Function:
Primarily we used Cross Entropy as our loss function. We experimented with an [additional penalty](https://github.com/akashe/Python-Code-Generation/blob/main/Original_data_with_penalty.ipynb) for code that fails execution but:
1. The new penalty based loss function make the training really slow because for each output in a batch we had to execute the script to get the result.
2. Model didn't learn. Since there is no way for the parameters to find gradients wrt to actual execution of the scripts, we multiplied it as a separate constant to the loss value. This changes the gradient value and naturally it didn't work. But we tried to see if we can atleast have some rudimentary learning which we can adjust with the punishment_constant we chose as a hyperparameter.

Python Embeddings:
We created [python embeddings](https://github.com/akashe/Python-Code-Generation/blob/main/Python_Embeddings_on_CoNaLa_mined_data.ipynb) using [CONALA mined dataset](https://conala-corpus.github.io/). The dataset consists of 590763 snippets of python. We train Decoder only transformer architecture and train it in an autoregressive manner. The task is simple to predict the next word given an input token. We train embeddings for a total of 15018 tokens which we got after using pythons in built tokenizer. 

Data Expansion:
In addition to 3100 examples from the original data we add additional 2800 examples from conala-train and conala-test datasets. The datasets are of same format with a natural language prompt for a python code and the corresponding python snippet.

Architecture:
Architecture is same as mentioned in the paper ["Attention is all you need."](https://arxiv.org/abs/1706.03762)

Evaluation metrics:

Experiments:

1. Vanilla encoder-decoder architecture:
    * Tokenizer for python code: normal python tokenizer with character level vocab for strings
    * encoder decoder architectures
    * Criterion: Cross Entropy loss
    
2. Pretrained embeddings for encoder and decoder.
   * Embedding for python code:
      0. Training embeddings on mined CONALA data
      1. BPE
      2. XLNET: autoencoding formulation?
      3. 
3. Encoder- Decoder architecture
    * with conala train + test data +original data
    * special error if python tokenizer gives error.
    
4. Char vocab
    
Example Outputs:


Attention graph between text and python code

Reference paper:
https://arxiv.org/pdf/2002.05442.pdf

from subword_nmt import apply_bpe
import codecs
import json

# 加载BPE规则
with codecs.open('vocab/bpecode.en', 'r', 'utf-8') as f:
    bpe = apply_bpe.BPE(f)

# 加载词汇表
#with codecs.open('vocab/vocen.json', 'r', 'utf-8') as f:
#    vocab = json.load(f)
with open('vocab/vocen.json', 'r', encoding='utf-8') as f:
    vocab = [line.strip() for line in f]


# 对输入的句子进行分词
sentence = "The sun is shining. The birds are singing. I love to walk in the park. The flowers are beautiful. Children play and laugh. It's a nice day"
#output = bpe.process_line(sentence)
output = bpe.segment_tokens(sentence.split())
print(output)

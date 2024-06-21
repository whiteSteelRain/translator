from sacremoses import MosesTokenizer, MosesDetokenizer,MosesTruecaser,MosesDetruecaser
from subword_nmt import apply_bpe
import codecs
import jieba
import ctranslate2
import re
source_text_en = "We can't waste food."
source_text_zh = "他在吃柠檬，小鸟在唱歌"


#1、中文：jieba
jieba.load_userdict('en2zh_data/dict.zh.txt')
zh_words = list(jieba.cut(source_text_zh))

zh_words = ' '.join(zh_words)

#2、中英文：tokenize

#英文
mt_en = MosesTokenizer(lang='en')
en_tok = mt_en.tokenize(source_text_en)#返回一个字符串
#['We', 'can', '&apos;t', 'waste', 'food', '.']

#中文：
mt_zh = MosesTokenizer(lang='zh')
zh_tok = mt_zh.tokenize(zh_words)




#4、中英文：bpe,这一步的作用是再细分
with codecs.open('vocab/bpecode.en', 'r', 'utf-8') as f:
    bpe_en_f = apply_bpe.BPE(f)
with codecs.open('vocab/bpecode.zh', 'r', 'utf-8') as f:
    bpe_zh_f = apply_bpe.BPE(f)    


bpe_en = bpe_en_f.segment_tokens(en_tok)
bpe_zh = bpe_zh_f.segment_tokens(zh_tok)

# #5、返回一个列表，里面装着传给翻译器的东西，即预处理后的文本输入部分。
# print('en:',bpe_en)
# print('zh:',bpe_zh)
# print('\n')

#----------------翻译
trans_en = ctranslate2.Translator(model_path = "zh_en_cmodel/", device="cpu") #en2zh
trans_zh = ctranslate2.Translator("en_zh_cmodel/", device="cpu")


answer_en_raw = trans_en.translate_batch([bpe_en])[0].hypotheses[0]
answer_zh_raw = trans_zh.translate_batch([bpe_zh])[0].hypotheses[0]



#8、detokenize，输出文本。
md_en = MosesDetokenizer(lang='zh')
md_zh = MosesDetokenizer(lang='en')

answer_en_bpe = md_en.detokenize(answer_en_raw,return_str=True)
answer_zh_bpe = md_zh.detokenize(answer_zh_raw,return_str=True)

answer_en = re.sub(r"@@ ", "",answer_en_bpe)
answer_zh = re.sub(r"@@ ", "",answer_zh_bpe)
print(answer_en,answer_zh)

























# # 加载BPE规则
# with codecs.open('vocab/bpecode.en', 'r', 'utf-8') as f:
#     bpe = apply_bpe.BPE(f)

# mt = MosesTokenizer(lang='en')
# text = 'we can\'t waste food'
# # expected_tokenized = 'This , is a sentence with weird \xbb symbols \u2026 appearing everywhere \xbf'
# tokenized_text = mt.tokenize(text, return_str=True)
# #print(tokenized_text)

# # Loads a model and truecase a string using trained model.
# mtr = MosesTruecaser('truecase-model.en')

# a = mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES", return_str=True)
# #print(a)

# mtd = MosesDetruecaser()
# b = mtd.detruecase('THE ADVENTURES OF SHERLOCK HOLMES',return_str=True)
# #print(a,b)
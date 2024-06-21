from sacremoses import MosesTokenizer, MosesDetokenizer,MosesTruecaser,MosesDetruecaser
from subword_nmt import apply_bpe
import codecs
import jieba
import ctranslate2
import re
source_text_en = "It’s a great time for me and my brethren fat cells. After millennia of toeing the line and giving up our stores whenever the muscles and nerves called on us, we’re now taking over. You don’t have to take my word for it. You can see it on the streets every day. More than 35 percent of adult Americans are obese. Not just overweight—obese. Cardiovascular disease? Type 2 diabetes? Cancer? Not my problem. I’m livin’ large.By 11 a.m.,The Body’s starving. That muffin he had for breakfast provided plenty of calories, but they don’t satisfy him the way they used to. See, it’s my job to send a hormone signal—called leptin—to the brain so it makes The Body feel full. It used to work like a charm. But these days, I pump leptin like it’s a Middle Eastern oil well, and it just floats around in the bloodstream, aimless. With all that excess insulin swirling around to help The Body sop up his extra sugar intake, the brain doesn’t receive my usual leptin signal and issue the “you’re stuffed, stop eating” message. So he’s more apt to feel hungry soon after he finishes eating.Life is sweet—saccharine, really. But it wasn’t always. I remember 40 years ago (The Body was barely a teenager) when I was born along with many of my fatty friends (puberty, the school nurse called it, which is when most adult fat cells should finish forming). "
source_text_zh = "我不明白，为什么大家都在谈论着项羽被困垓下，仿佛这中原古战场对于我们注定了凶多吉少。二十年前，我从徐州踏上征途，开始了第二次北伐，中华秋海棠叶遂归于一统。本党本军所到之处，民众竭诚欢迎，真可谓占尽天时，那种勃勃生机万物竞发的境界犹在眼前。短短二十年后，这里竟至于一变而为我的葬身之地了吗？"


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


#3、英文：truecaser,实测不行，truecase训练的有问题
#mtr_en = MosesTruecaser('truecase-model.en')
#en_tok_true = mtr_en.truecase(str(en_tok))
en_tok_true = en_tok

#4、中英文：bpe,这一步的作用是再细分
with codecs.open('vocab/bpecode.en', 'r', 'utf-8') as f:
    bpe_en_f = apply_bpe.BPE(f)
with codecs.open('vocab/bpecode.zh', 'r', 'utf-8') as f:
    bpe_zh_f = apply_bpe.BPE(f)    


bpe_en = bpe_en_f.segment_tokens(en_tok_true)
bpe_zh = bpe_zh_f.segment_tokens(zh_tok)

#5、返回一个列表，里面装着传给翻译器的东西，即预处理后的文本输入部分。
print('en:',bpe_en)
print('zh:',bpe_zh)
print('\n')

#----------------翻译
trans_en = ctranslate2.Translator(model_path = "zh_en_cmodel/", device="cpu") #en2zh
trans_zh = ctranslate2.Translator("en_zh_cmodel/", device="cpu")



temp_en = trans_en.translate_batch([bpe_en])
answer_en_raw = ''.join(temp_en[0].hypotheses[0])
temp_zh = trans_zh.translate_batch([bpe_zh])
answer_zh_raw = temp_zh[0].hypotheses[0] #''.join(temp_zh[0].hypotheses[0])
#answer_zh_raw = ' '.join(answer_zh_raw)
print(answer_zh_raw)
#6、中英文：翻译过后，先去掉bpe符号@@之类的
answer_en_nobpe = re.sub(r"@@ ", "",answer_en_raw)
#answer_zh_nobpe = re.sub(r"@@ ", "",answer_zh_raw)
#print(type(answer_zh_nobpe))
#print(answer_en_nobpe,answer_zh_nobpe)
#7、英文：再detruecase，把大小写恢复原样
#mtd = MosesDetruecaser()
#answer_en_de = mtd.detruecase(answer_en_nobpe)
#print(answer_en_de)
answer_en_de = answer_en_nobpe

#8、detokenize，输出文本。
md_en = MosesDetokenizer(lang='zh')
md_zh = MosesDetokenizer(lang='en')

answer_en = md_en.detokenize(answer_en_de,return_str=True)
answer_zh_nobpe = md_zh.detokenize(answer_zh_raw,return_str=True)
answer_zh = re.sub(r"@@ ", "",answer_zh_nobpe)
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
from sacremoses import MosesTokenizer, MosesDetokenizer,MosesTruecaser,MosesDetruecaser
from subword_nmt import apply_bpe
import codecs
import jieba
import ctranslate2
import re

def fairseq(source_zh,source_en):
    中文 = True#这一句替换为英汉选项逻辑

    #中文部分初始化，词典的导入等等
    jieba.load_userdict('en2zh_data/dict.zh.txt')
    mt_zh = MosesTokenizer(lang='zh')
    with codecs.open('vocab/bpecode.zh', 'r', 'utf-8') as f:
        bpe_zh_f = apply_bpe.BPE(f)  
    trans_zh = ctranslate2.Translator("en_zh_cmodel/", device="cpu")
    md_zh = MosesDetokenizer(lang='en')

    #英文部分初始化，定义tokenize等等
    md_en = MosesDetokenizer(lang='zh')
    trans_en = ctranslate2.Translator(model_path = "zh_en_cmodel/", device="cpu")   #en2zh
    mt_en = MosesTokenizer(lang='en')
    with codecs.open('vocab/bpecode.en', 'r', 'utf-8') as f:
        bpe_en_f = apply_bpe.BPE(f)
    #分词开始
    if(中文 is True):
        zh_words = list(jieba.cut(source_zh))
        zh_words = ' '.join(zh_words)
        zh_tok = mt_zh.tokenize(zh_words)
        bpe_zh = bpe_zh_f.segment_tokens(zh_tok)
        answer_zh_raw = trans_zh.translate_batch([bpe_zh])[0].hypotheses[0]
        answer_zh_bpe = md_zh.detokenize(answer_zh_raw,return_str=True)
        answer_zh = re.sub(r"@@ ", "",answer_zh_bpe) 
        return answer_zh
    else: 
        en_tok = mt_en.tokenize(source_en)
        bpe_en = bpe_en_f.segment_tokens(en_tok)
        answer_en_raw = trans_en.translate_batch([bpe_en])[0].hypotheses[0]
        answer_en_bpe = md_en.detokenize(answer_en_raw,return_str=True)
        answer_en = re.sub(r"@@ ", "",answer_en_bpe)
        return answer_en
       



    
    

    













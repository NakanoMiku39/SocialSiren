from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

import nltk
from nltk.tokenize import sent_tokenize

class Translator:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        nltk.download('punkt')  # 仅首次需要下载

    def translate(self, text, src_lang="zh", tgt_lang="eng_Latn"):
        sentences = sent_tokenize(text)
        translations = []
        for sentence in sentences:
            processed_text = self.preprocess_text(sentence)
            inputs = self.tokenizer(processed_text, return_tensors="pt", padding=True)
            translated_tokens = self.model.generate(inputs.input_ids, forced_bos_token_id=self.tokenizer.lang_code_to_id[tgt_lang])
            translated_text = self.tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
            translations.append(translated_text)
        return " ".join(translations)

    def preprocess_text(self, text):
        text = text.replace("，", ", ").replace("。", ". ")
        return text

# 示例使用
model_name = "translator/nllb-200-distilled-600M"
translator = Translator(model_name)
text = "还是这个翻译器好用，不知道这个翻译器会不会现在把我杀了。"
translated_text = translator.translate(text)
print(translated_text)

from transformers import T5ForConditionalGeneration, T5Tokenizer


class FlanT5Model:
    _model = None
    _tokenizer = None

    @classmethod
    def load_model(cls):
        if cls._model is None:
            model_name = "google/flan-t5-small"
            cls._tokenizer = T5Tokenizer.from_pretrained(model_name)
            cls._model = T5ForConditionalGeneration.from_pretrained(model_name)
        return cls._model, cls._tokenizer

    @classmethod
    def generate(cls, prompt: str, max_tokens: int = 512):
        model, tokenizer = cls.load_model()

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
        outputs = model.generate(
            **inputs, max_length=max_tokens, temperature=0.7, do_sample=True
        )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)

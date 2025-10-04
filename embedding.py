#This file isn't really being used
from sentence_transformers import SentenceTransformer

input_texts = [
    'query: how much protein should a female eat',
    'query: summit define',
    "passage: As a general guideline, the CDC's average requirement of protein for women ages 19 to 70 is 46 grams per day. But, as you can see from this chart, you'll need to increase that if you're expecting or training for a marathon. Check out the chart below to see how much protein you should be eating each day.",
    "passage: Definition of summit for English Language Learners. : 1  the highest point of a mountain : the top of a mountain. : 2  the highest level. : 3  a meeting or series of meetings between the leaders of two or more governments."
]

def get_embeddings(texts: list[str], model_name: str = "intfloat/e5-small-v2", normalize: bool = True):
    model = SentenceTransformer(model_name)
    return model.encode(texts, normalize_embeddings=normalize)

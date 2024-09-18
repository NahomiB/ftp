from openai import OpenAI
from helper.logguer import log_message
import tiktoken
import numpy as np

def cosine_similarity(embedding1, embedding2):
    """
    Calcula la similitud del coseno entre dos embeddings.

    :param embedding1: Primer embedding (vector).
    :param embedding2: Segundo embedding (vector).
    :return: Similitud del coseno entre los dos embeddings.
    """
    dot_product = np.dot(embedding1, embedding2)
    norm_embedding1 = np.linalg.norm(embedding1)
    norm_embedding2 = np.linalg.norm(embedding2)

    if norm_embedding1 == 0 or norm_embedding2 == 0:
        return 0.0  # Evitar división por cero

    return dot_product / (norm_embedding1 * norm_embedding2)

client = OpenAI(base_url="http://host.docker.internal:1234/v1", api_key="lm-studio")


def get_embedding(text, model="nomic-ai/nomic-embed-text-v1.5-GGUF"):
    text = text.replace("\n", " ")
    response=client.embeddings.create(input=[text], model=model)
    print(response.usage.total_tokens)
    
    return response.data[0].embedding



def split_text(text, model='gpt-3.5-turbo', max_tokens=512):
    # Load the encoder for the specified model
    enc = tiktoken.encoding_for_model(model)
    
    # Encode the text into tokens
    tokens = enc.encode(text)
    
    # Split the tokens into chunks of maximum size
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    
    # Decode the token chunks back into text
    text_chunks = [enc.decode(chunk) for chunk in chunks]
    
    return text_chunks, len(tokens)



def create_embedding(text:str)->tuple[list[np.array],list[str]]:
    """
    Dado el texto crea el array de embeddings para guardarlos

    Args:
        text (str): _description_

    Returns:
      tuple[list[np.array],list[str]] : lista que tiene en cada indice los embeddings dd los chunks y los pedazos del embedding
    """
    log_message(f'Se va crear el embedding del {text}',func=create_embedding)
    chunks,len_tokens=split_text(text,max_tokens=1950)
    log_message(f"El embedding del {text} tiene {len_tokens} tokens",func=create_embedding)
    lis=[]
    list_text_chunks:list[str]=chunks
    for chunk in chunks:
        embedding=get_embedding(chunk)
        lis.append(np.array(embedding))
    log_message(f"Este es la lista de embeddings del {text} list: {lis}",func=create_embedding)
    return lis,list_text_chunks
import pinecone
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from uuid import uuid4
from dotenv import load_dotenv, dotenv_values
import os

# load env variables
load_dotenv()

pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_region = os.getenv("PINECONE_REGION")
open_ai_key = os.getenv("OPENAI_API_KEY")

pinecone.init(api_key=pinecone_api_key, environment=pinecone_region)
pinecone_index = "yt-transcribe"

model_name = 'text-embedding-ada-002'

# create the length function
# def calculate_token_length(text):
#     # initializing tokenizer
#     tokenizer = tiktoken.get_encoding('p50k_base')
#     tokens = tokenizer.encode(
#         str(text),
#         disallowed_special=()
#     )
#     return len(tokens)



def store_transcribe_to_pinecone(url, vId):
    try:
        # read from file
        file_path = os.path.join("subtitle",f"{vId}.txt")
        
        # Read from the file
        with open(file_path, "r") as file:
            file_contents = file.read()
        
        # getting length of our data in tokens
        # token_length = calculate_token_length(file_contents)
        # print(token_length)
        
        # deleting subtitle file
        os.remove(file_path)
        
        # split our text to small chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=0,
        )
        chunks = text_splitter.split_text(file_contents)
        # print("\n###### CHUNKS #######\n", chunks)
        # lets create metadata
        metadata=[]
        for i, chunk in enumerate(chunks):
            metadata.append({
                "chunk":i,
                "text":chunk,
                "url":url,
                "video_id":vId
            })
        # print(metadata)
        
        # basically generates a vector of vectors where each vector represents an embedding
        embed = OpenAIEmbeddings(
            model=model_name,
        openai_api_key=open_ai_key
        )
        
        embeddings_vector = embed.embed_documents(chunks)
        ids = [str(uuid4()) for _ in range(len(chunks))]
        
        # insert embeddings inside the db
        index = pinecone.Index(pinecone_index)
        print("\nBefore Storing Status Of Pinecone Index\n",index.describe_index_stats())
        index.upsert(vectors=zip(ids, embeddings_vector, metadata))
        print("\nAfter Storing Status Of Pinecone Index\n",index.describe_index_stats())
    except Exception as e:
        raise Exception(e)
    except OSError as oe:
        raise Exception(oe)

import pinecone
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
import os

pinecone.init()
pinecone_index = "yt-transcribe"

model_name = 'text-embedding-ada-002'

# create the length function
def calculate_token_length(text):
    # initializing tokenizer
    tokenizer = tiktoken.get_encoding('p50k_base')
    tokens = tokenizer.encode(
        str(text),
        disallowed_special=()
    )
    return len(tokens)



def store_transcribe_to_pinecone(url, vId):
    # read from file
    file_path = os.path.join("subtitle",f"{vId}.txt")
    
    # Read from the file
    with open(file_path, "r") as file:
        file_contents = file.read()
        # print("###############################################\n\n########################################################\n\n")
        print(type(file_contents))
    # data = {
    #     "transcript":transcript[0],
    #     "url":url,
    #     "video_id":vId
    # }
    
    # getting length of our data in tokens
    token_length = calculate_token_length(file_contents)
    print(token_length)
    
    # split our text to small chunks
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=20,
    length_function=token_length,
    separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(file_contents)
    print(chunks)
    
    # # pinecone.create_index(name=pinecone_index, dimension=1536)
    
    # embed = OpenAIEmbeddings(
    # document_model_name=model_name,
    # query_model_name=model_name,
    # openai_api_key=""
    # )
    
    # res = embed.embed_documents(chunks)
    # pinecone.index(index_name=pinecone_index, data=res, ids=None)
    # pinecone.deinit()


import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def test():
    embeddings = GoogleGenerativeAIEmbeddings(
        model="text-embedding-004",
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )
    res = embeddings.embed_query("test")
    print("Success, length:", len(res))

if __name__ == "__main__":
    test()

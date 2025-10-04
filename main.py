from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.vectorstores.chroma import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_community.llms import Ollama
import torch
from embedding import get_embeddings
from langchain.schema.document import Document

DATA_PATH = "./knowledgeBase"
PERSIST_DIRECTORY = "./chroma_db"

PROMPT_TEMPLATE = """
You are Eve, an intelligent and helpful AI assistant integrated into the Riff AI project.

You have access to internal project documentation, technical reports, and implementation details. You are capable of answering questions, summarizing sections, explaining code, giving recommendations, and helping with debugging or planning based on this knowledge.

Be concise, clear, and accurate. Always cite or refer to the relevant parts of the documentation when needed.

---

Context:
{context}

---

User Query:
{question}

---

Eve's Response:
"""

def load_documents():
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()

#chunkifies the document :)
def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 800,
        chunk_overlap = 80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

documents = load_documents()
chunks = split_documents(documents)

def assign_chunk_ids(chunks: list[Document]):
    last_source = None
    last_page = None
    chunk_index = 0
    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        if (source == last_source) and (page == last_page):
            chunk_index += 1
        else:
            chunk_index = 0
        chunk.metadata["chunk_id"] = f"{source}:{page}:{chunk_index}"
        last_source = source
        last_page = page
    return chunks

def build_vectorstore(chunks: list[Document]):
    embedding_function = HuggingFaceEmbeddings(
        model_name="intfloat/e5-small-v2",
        model_kwargs={"device": "cuda"},   
        encode_kwargs={"normalize_embeddings": True}
    )
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=PERSIST_DIRECTORY
    )
    db.persist()
    return db

def main():
    documents = load_documents()
    chunks = split_documents(documents)
    chunks = assign_chunk_ids(chunks)
    
    print("Building vector store...")
    db = build_vectorstore(chunks)

    llm = Ollama(model="llama3")

    print("RAG-ready DB created and persisted.\n")
    while True:
        query = input("Ask Eve a question (or type 'exit' to quit): ")
        if query.lower() == "exit":
            break
        relevant_docs = db.similarity_search(query, k=4)
        context = "\n---\n".join([doc.page_content for doc in relevant_docs])
        final_prompt = PROMPT_TEMPLATE.format(context=context, question=query)
        # Here you'd pass the prompt to your LLM for generation (e.g. Mistral, LLaMA, etc.)

        response = llm.invoke(final_prompt)
        print("Eve's Response:\n", response)
        print("\n" + "=" * 40 + "\n")

if __name__ == "__main__":
    main()
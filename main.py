from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.schema.document import Document

import torch
from embedding import get_embeddings  # your custom embedding function
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "knowledgeBase")
PERSIST_DIRECTORY = os.path.join(BASE_DIR, "chroma_db")

# --- Prompt template ---
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

# --- Global variables ---
db_lock = threading.Lock()
db = None  # global Chroma DB reference

# --- Functions ---

def load_documents():
    if not os.path.exists(DATA_PATH):
        print(f"ERROR: {DATA_PATH} does not exist. Please add PDFs to load.", flush=True)
        return []

    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    documents = document_loader.load()
    print(f"Loaded {len(documents)} documents.", flush=True)
    return documents

def split_documents(documents: list[Document]):
    if not documents:
        print("No documents to split.", flush=True)
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.", flush=True)
    return chunks

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
    if not chunks:
        print("No chunks available to build vectorstore.", flush=True)
        return None

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}", flush=True)

    embedding_function = HuggingFaceEmbeddings(
        model_name="intfloat/e5-small-v2",
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True}
    )

    db_instance = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=PERSIST_DIRECTORY
    )
    db_instance.persist()
    print(f"Vectorstore persisted at {PERSIST_DIRECTORY}", flush=True)
    return db_instance

def rebuild_db():
    """Reload documents and rebuild the vectorstore"""
    global db
    with db_lock:
        print("\n[Watcher] Rebuilding vectorstore...", flush=True)
        documents = load_documents()
        chunks = split_documents(documents)
        chunks = assign_chunk_ids(chunks)
        db = build_vectorstore(chunks)
        if db:
            print("[Watcher] Vectorstore rebuilt successfully.\n", flush=True)
        else:
            print("[Watcher] Failed to rebuild vectorstore.\n", flush=True)

# --- Watchdog handler ---
class KnowledgeBaseHandler(FileSystemEventHandler):
    def __init__(self, rebuild_callback):
        self.rebuild_callback = rebuild_callback

    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".pdf"):
            print(f"[Watcher] Change detected in knowledgeBase: {event.src_path}", flush=True)
            self.rebuild_callback()

def watch_knowledge_base(callback):
    event_handler = KnowledgeBaseHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, path=DATA_PATH, recursive=False)
    observer.start()
    return observer

# --- Main loop ---
def main():
    global db
    rebuild_db()  # Initial build

    # Start knowledgeBase watcher
    observer = watch_knowledge_base(rebuild_db)

    llm = Ollama(model="llama3")
    print("Eve is ready! Type your question or 'exit' to quit.", flush=True)

    try:
        while True:
            try:
                query = input()
                if query.lower() == "exit":
                    break

                with db_lock:
                    if db is None:
                        print("Vectorstore not ready yet. Please wait...", flush=True)
                        continue
                    relevant_docs = db.similarity_search(query, k=4)

                context = "\n---\n".join([doc.page_content for doc in relevant_docs])
                final_prompt = PROMPT_TEMPLATE.format(context=context, question=query)
                response = llm.invoke(final_prompt)
                print(response, flush=True)

            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}", flush=True)
    finally:
        observer.stop()
        observer.join()

# --- Entry point ---
if __name__ == "__main__":
    main()

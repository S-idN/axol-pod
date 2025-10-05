# --- Imports ---
# Standard library imports
import os
import sys

# Third-party imports for Flask
from flask import Flask, request, jsonify
from flask_cors import CORS

# LangChain and other AI library imports
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.vectorstores.chroma import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.schema.document import Document

# --- Constants ---
DATA_PATH = "./knowledgeBase"
PERSIST_DIRECTORY = "./chroma_db"
EMBEDDING_MODEL = "intfloat/e5-small-v2"
LLM_MODEL = "llama3"
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

# --- Helper Functions (from your original script) ---
def load_documents():
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

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

# --- Core Application Setup ---
# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Global variables to hold the database and LLM
# This ensures they are loaded only ONCE when the server starts.
db = None
llm = None

def initialize_rag_pipeline():
    """
    Initializes the RAG pipeline by loading/building the vector store and loading the LLM.
    This function is called once at startup.
    """
    global db, llm
    
    # Initialize embedding function
    embedding_function = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True}
    )

    # Check if the vector store already exists
    if os.path.exists(PERSIST_DIRECTORY):
        print("Loading existing Chroma vector store...")
        db = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding_function)
    else:
        print("Existing vector store not found. Building a new one...")
        # Check if the knowledgeBase directory exists
        if not os.path.exists(DATA_PATH) or not os.listdir(DATA_PATH):
             print(f"Error: The '{DATA_PATH}' directory is empty or does not exist.")
             print("Please add your PDF files to it and restart the server.")
             sys.exit(1) # Exit the script if there's no data to process
        
        documents = load_documents()
        chunks = split_documents(documents)
        chunks = assign_chunk_ids(chunks)
        
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_function,
            persist_directory=PERSIST_DIRECTORY
        )
        db.persist()
        print("New vector store built and persisted.")

    # Load the LLM
    print("Loading LLM...")
    llm = Ollama(model=LLM_MODEL)
    print("RAG pipeline is ready.")

# --- API Endpoint ---
@app.route('/ask', methods=['POST'])
def ask_eve():
    """
    This is the main API endpoint that the Electron app will call.
    It replaces the `while True` loop from your original script.
    """
    if not request.json or 'query' not in request.json:
        return jsonify({"error": "Invalid request. 'query' field is required."}), 400

    query = request.json['query']
    print(f"Received query: {query}", file=sys.stderr)

    if not db or not llm:
        return jsonify({"error": "RAG pipeline is not initialized."}), 500

    try:
        # 1. Retrieve relevant documents
        relevant_docs = db.similarity_search(query, k=4)
        context = "\n---\n".join([doc.page_content for doc in relevant_docs])

        # 2. Format the prompt
        final_prompt = PROMPT_TEMPLATE.format(context=context, question=query)

        # 3. Get the response from the LLM
        response = llm.invoke(final_prompt)
        print(f"Generated response: {response}", file=sys.stderr)

        # 4. Return the response as JSON
        return jsonify({"response": response})

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

# --- Main Execution ---
if __name__ == '__main__':
    initialize_rag_pipeline()
    # Run the Flask app on a specific port
    app.run(host='0.0.0.0', port=5123, debug=False)
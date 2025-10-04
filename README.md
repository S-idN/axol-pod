# axol-pod

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)

A RAG-based AI agent for querying local PDFs and files using LangChain and a ChromaDB vector store. It's designed to be private, efficient, and run entirely on your local machine.

---

> **Note**: This project is currently in its initial development phase.

## About The Project

**axol-pod** allows you to transform your personal documents into an intelligent, queryable knowledge base. Ever wanted to ask questions about a textbook, a research paper, or a set of meeting notes? This tool ingests your files, stores them efficiently, and uses a local AI agent to provide context-aware answers, ensuring your data remains completely private.

## Key Features

- **💬 Chat With Your Documents**: Ask questions in natural language and get answers based on the content of your files.
- **🔒 Private & Local-First**: Your documents and queries never leave your computer.
- **🧠 Powered by RAG**: Utilizes a Retrieval-Augmented Generation pipeline for accurate, context-rich responses.
- **📄 PDF & Text Support**: Easily ingest `.pdf`, `.txt`, and `.md` files.
- **🧩 Modular Design**: Built with LangChain for easy modification and extension.

## Tech Stack

This project is built with a modern Python AI stack:

- **Framework**: [LangChain](https://www.langchain.com/)
- **LLM**: [Llama 3](https://ollama.com/library/llama3) (via Ollama) or any other local LLM
- **Embeddings**: [Hugging Face Transformers](https://huggingface.co/sentence-transformers)
- **Vector Store**: [ChromaDB](https://www.trychroma.com/)
- **Core Language**: Python

---

## Getting Started

Follow these steps to get a local copy up and running.

### Prerequisites

- Python 3.9+
- Git
- [Ollama](https://ollama.com/) installed and running with your desired model (e.g., `ollama run llama3`).

### Installation

1.  **Clone the repository:**

    ```sh
    git clone [https://github.com/your-username/axol-pod.git](https://github.com/your-username/axol-pod.git)
    cd axol-pod
    ```

2.  **Create and activate a virtual environment:**

    ```sh
    # For Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # For macOS / Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4.  **Add Your Documents:**

    - Create a folder named `documents` in the root of the project.
    - Place all your PDF or text files inside this `documents` folder.

5.  **Ingest the Data:**
    Run the ingestion script to process your documents and build the vector store.
    ```sh
    python ingest.py
    ```
    This only needs to be done once, or whenever you add new documents.

---

## Usage

Once you have ingested your documents, you can start the conversational agent.

1.  **Run the main application:**

    ```sh
    python main.py
    ```

2.  **Start asking questions!**
    You'll see a prompt. Type your question and press Enter. The agent will use your documents to find the answer.

    ```
    Ask Eve a question (or type 'exit' to quit): hi eve

    Eve's Response:
    Hi! I'm Eve, your AI assistant from the Riff project. How can I help you today? Would you like to discuss something specific about the emotional music graph feature, or perhaps explore a technical aspect of our tech stack? Let me know, and I'll do my best to assist you!

    ========================================

    Ask Eve a question (or type 'exit' to quit): exit
    ```

---

## Project Roadmap

- [ ] Integrate a custom-trained model for more specialized responses.
- [ ] Add support for more file types (e.g., `.docx`, `.pptx`).
- [ ] Implement conversation history for follow-up questions.

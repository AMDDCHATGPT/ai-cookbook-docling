# Building Knowledge Extraction Pipeline with Docling

[Docling](https://github.com/DS4SD/docling) is a powerful, flexible open source document processing library that converts various document formats into a unified format. It has advanced document understanding capabilities powered by state-of-the-art AI models for layout analysis and table structure recognition.

The whole system runs locally on standard computers and is designed to be extensible - developers can add new models or modify the pipeline for specific needs. It's particularly useful for tasks like enterprise document search, passage retrieval, and knowledge extraction. With its advanced chunking and processing capabilities, it's the perfect tool for providing GenAI applications with knowledge through RAG (Retrieval Augmented Generation) pipelines.

## Key Features

- **Universal Format Support**: Process PDF, DOCX, XLSX, PPTX, Markdown, HTML, images, and more
- **Advanced Understanding**: AI-powered layout analysis and table structure recognition
- **Flexible Output**: Export to HTML, Markdown, JSON, or plain text
- **High Performance**: Efficient processing on local hardware

## Things They're Working on

- Metadata extraction, including title, authors, references & language
- Inclusion of Visual Language Models (SmolDocling)
- Chart understanding (Barchart, Piechart, LinePlot, etc)
- Complex chemistry understanding (Molecular structures)

## Getting Started with the Example

### Prerequisites

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables by creating a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

### Running the Example

Execute the files in order to build and query the document database:

1. Extract document content: `python 1-extraction.py`
2. Create document chunks: `python 2-chunking.py`
3. Create embeddings and store in LanceDB: `python 3-embedding.py`
4. Test basic search functionality: `python 4-search.py`
5. Launch the Streamlit chat interface: `streamlit run 5-chat.py`

Then open your browser and navigate to `http://localhost:8501` to interact with the document Q&A interface.

## Document Processing

### Supported Input Formats

| Format | Description |
|--------|-------------|
| PDF | Native PDF documents with layout preservation |
| DOCX, XLSX, PPTX | Microsoft Office formats (2007+) |
| Markdown | Plain text with markup |
| HTML/XHTML | Web documents |
| Images | PNG, JPEG, TIFF, BMP |
| USPTO XML | Patent documents |
| PMC XML | PubMed Central articles |

Check out this [page](https://ds4sd.github.io/docling/supported_formats/) for an up to date list.

### Processing Pipeline

The standard pipeline includes:

1. Document parsing with format-specific backend
2. Layout analysis using AI models
3. Table structure recognition
4. Metadata extraction
5. Content organization and structuring
6. Export formatting

## Models

Docling leverages two primary specialized AI models for document understanding. At its core, the layout analysis model is built on the `RT-DETR (Real-Time Detection Transformer)` architecture, which excels at detecting and classifying page elements. This model processes pages at 72 dpi resolution and can analyze a single page in under a second on a standard CPU, having been trained on the comprehensive `DocLayNet` dataset.

The second key model is `TableFormer`, a table structure recognition system that can handle complex table layouts including partial borders, empty cells, spanning cells, and hierarchical headers. TableFormer typically processes tables in 2-6 seconds on CPU, making it efficient for practical use. 

For documents requiring text extraction from images, Docling integrates `EasyOCR` as an optional component, which operates at 216 dpi for optimal quality but requires about 30 seconds per page. Both the layout analysis and TableFormer models were developed by IBM Research and are publicly available as pre-trained weights on Hugging Face under "ds4sd/docling-models".

For more detailed information about these models and their implementation, you can refer to the [technical documentation](https://arxiv.org/pdf/2408.09869).

## Chunking

When you're building a RAG (Retrieval Augmented Generation) application, you need to break down documents into smaller, meaningful pieces that can be easily searched and retrieved. But this isn't as simple as just splitting text every X words or characters.

What makes [Docling's chunking](https://ds4sd.github.io/docling/concepts/chunking/) unique is that it understands the actual structure of your document. It has two main approaches:

1. The [Hierarchical Chunker](https://ds4sd.github.io/docling/concepts/chunking/#hierarchical-chunker) is like a smart document analyzer - it knows where the natural "joints" of your document are. Instead of blindly cutting text into fixed-size pieces, it recognizes and preserves important elements like sections, paragraphs, tables, and lists. It maintains the relationship between headers and their content, and keeps related items together (like items in a list).

2. The [Hybrid Chunker](https://ds4sd.github.io/docling/concepts/chunking/#hybrid-chunker) takes this a step further. It starts with the hierarchical chunks but then:
   - It can split chunks that are too large for your embedding model
   - It can stitch together chunks that are too small
   - It works with your specific tokenizer, so the chunks will fit perfectly with your chosen language model

### Why is this great for RAG applications?

Imagine you're building a system to answer questions about technical documents. With basic chunking (like splitting every 500 words), you might cut right through the middle of a table, or separate a header from its content. But Docling's smart chunking:

- Keeps related information together
- Preserves document structure
- Maintains context (like headers and captions)
- Creates chunks that are optimized for your specific embedding model
- Ensures each chunk is meaningful and self-contained

This means when your RAG system retrieves chunks, they'll have the proper context and structure, leading to more accurate and coherent responses from your language model.

## Documentation

For full documentation, visit [documentation site](https://ds4sd.github.io/docling/).

For example notebooks and more detailed guides, check out [GitHub repository](https://github.com/DS4SD/docling).

## Interactive Upload & Processing in Streamlit (New)

In addition to the numbered step scripts, you can now upload and process documents directly through the Streamlit interface for a more interactive experience.

### Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment:
```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

3. Launch the interactive application:
```bash
streamlit run 5-chat.py
```

### Interactive Workflow

The Streamlit app now includes a sidebar with document management features:

1. **Document Upload**: Upload multiple files (PDF, DOCX, PPTX, XLSX, Markdown, HTML, TXT) using the file uploader
2. **Automatic Processing**: Click "Process Documents" to automatically:
   - Convert documents using Docling's DocumentConverter
   - Create chunks using HybridChunker with OpenAI tokenizer
   - Generate embeddings using OpenAI's text-embedding-3-large
   - Store everything in LanceDB for fast retrieval
3. **Smart Deduplication**: Files are tracked in session state to avoid re-processing the same document multiple times
4. **Real-time Stats**: View knowledge base statistics including total chunks and list of ingested files
5. **Enhanced Chat**: Ask questions with improved context-only responses and vector similarity search

### Storage Locations

- **Uploaded Files**: Stored in `data/uploads/` directory
- **Vector Database**: LanceDB database stored in `data/lancedb/` directory
- **Embeddings**: Generated using OpenAI's text-embedding-3-large model

### Features

- **Multi-format Support**: Process various document types seamlessly
- **Progress Tracking**: Real-time feedback during document processing
- **Per-file Statistics**: See how many chunks were created for each document
- **Context-focused Responses**: AI responses are now more precise and only use information from uploaded documents
- **Session Management**: Clear chat history and track processed files
- **Error Handling**: Graceful handling of processing failures with detailed feedback

### Important Notes

- **API Key Required**: You need a valid OpenAI API key for embeddings and chat functionality
- **Session-based Deduplication**: File tracking is per-session; restarting the app allows re-processing of previously uploaded files
- **Local Storage**: All files and data remain on your local machine for privacy and security
- **No Multi-user Support**: This is designed for single-user local usage

### Troubleshooting

- **"No documents ingested yet"**: Upload and process documents using the sidebar before asking questions
- **Empty responses**: Ensure your question relates to content in the uploaded documents
- **Processing failures**: Check file formats are supported and files aren't corrupted
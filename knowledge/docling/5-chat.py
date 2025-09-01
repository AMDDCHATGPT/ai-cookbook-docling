import streamlit as st
import lancedb
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from utils.pipeline import process_documents, get_table_stats, get_or_create_table

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()


# Initialize LanceDB connection
@st.cache_resource
def init_db():
    """Initialize database connection.

    Returns:
        LanceDB table object
    """
    return get_or_create_table("data/lancedb", "docling")


def get_context(query: str, table, num_results: int = 5) -> str:
    """Search the database for relevant context.

    Args:
        query: User's question
        table: LanceDB table object
        num_results: Number of results to return

    Returns:
        str: Concatenated context from relevant chunks with source information
    """
    # Use explicit vector similarity search
    results = table.search(query, query_type="vector").limit(num_results).to_pandas()
    contexts = []

    for _, row in results.iterrows():
        # Extract metadata
        filename = row["metadata"]["filename"]
        page_numbers = row["metadata"]["page_numbers"]
        title = row["metadata"]["title"]

        # Build source citation
        source_parts = []
        if filename:
            source_parts.append(filename)
        if page_numbers:
            source_parts.append(f"p. {', '.join(str(p) for p in page_numbers)}")

        source = f"\nSource: {' - '.join(source_parts)}"
        if title:
            source += f"\nTitle: {title}"

        contexts.append(f"{row['text']}{source}")

    return "\n\n".join(contexts)


def get_chat_response(messages, context: str) -> str:
    """Get streaming response from OpenAI API.

    Args:
        messages: Chat history
        context: Retrieved context from database

    Returns:
        str: Model's response
    """
    system_prompt = f"""You are a helpful assistant that answers questions based strictly on the provided context.
    Use only the information from the context to answer questions. If you're unsure or the context
    doesn't contain the relevant information, clearly state that you cannot answer based on the available context.
    Be precise and only cite information that is explicitly mentioned in the context.
    
    Context:
    {context}
    """

    messages_with_context = [{"role": "system", "content": system_prompt}, *messages]

    # Create the streaming response with lower temperature for more focused answers
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_with_context,
        temperature=0.4,
        stream=True,
    )

    # Use Streamlit's built-in streaming capability
    response = st.write_stream(stream)
    return response


# Initialize Streamlit app
st.title("📚 Document Q&A")

# Initialize session state for chat history and processed files
if "messages" not in st.session_state:
    st.session_state.messages = []

if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

# Initialize database connection
table = init_db()

# Sidebar for file upload and management
with st.sidebar:
    st.header("📁 Document Management")
    
    # File upload section
    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'pptx', 'xlsx', 'md', 'html', 'txt'],
        help="Supported formats: PDF, DOCX, PPTX, XLSX, Markdown, HTML, TXT"
    )
    
    # Process uploaded files
    if uploaded_files:
        new_files = []
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.processed_files:
                new_files.append(uploaded_file)
        
        if new_files and st.button("Process Documents", type="primary"):
            # Save uploaded files and process them
            uploaded_paths = []
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            for uploaded_file in new_files:
                file_path = upload_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                uploaded_paths.append(str(file_path))
            
            # Process documents with progress indicator
            with st.status("Processing documents...", expanded=True) as status:
                st.write("Converting and chunking documents...")
                stats = process_documents(uploaded_paths)
                
                # Display processing results
                st.write(f"📊 **Processing Complete!**")
                st.write(f"- Files processed: {stats['files_processed']}")
                st.write(f"- Total chunks created: {stats['total_chunks']}")
                
                # Show per-file results
                if stats['per_file_stats']:
                    st.write("**Per-file results:**")
                    for file_stat in stats['per_file_stats']:
                        if file_stat['status'] == 'success':
                            st.write(f"✅ {file_stat['filename']}: {file_stat['chunks']} chunks")
                        else:
                            st.write(f"❌ {file_stat['filename']}: {file_stat['status']}")
                
                if stats['failed_files']:
                    st.warning(f"Failed to process {len(stats['failed_files'])} files")
                
                status.update(label="✅ Processing complete!", state="complete")
            
            # Update session state with processed files
            for uploaded_file in new_files:
                st.session_state.processed_files.add(uploaded_file.name)
            
            # Refresh the table connection
            st.cache_resource.clear()
            table = init_db()
        
        elif new_files:
            st.info(f"Ready to process {len(new_files)} new file(s)")
        else:
            st.info("All uploaded files have already been processed in this session")
    
    # Vector store statistics
    st.subheader("📊 Knowledge Base Stats")
    try:
        table_stats = get_table_stats()
        st.metric("Total Chunks", table_stats["total_rows"])
        
        if table_stats["unique_files"]:
            st.write("**Ingested Files:**")
            for filename in sorted(table_stats["unique_files"]):
                st.write(f"📄 {filename}")
        else:
            st.write("No documents ingested yet")
    except Exception:
        st.write("Vector store not initialized")
    
    # Chat management
    st.subheader("💬 Chat Management")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Check if there are any documents in the knowledge base
table_stats = get_table_stats()
if table_stats["total_rows"] == 0:
    st.warning("👆 Please upload and process some documents using the sidebar before asking questions!")

# Chat input
if prompt := st.chat_input("Ask a question about the documents", disabled=(table_stats["total_rows"] == 0)):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get relevant context
    with st.status("Searching documents...", expanded=False) as status:
        context = get_context(prompt, table)
        
        if not context.strip():
            st.warning("No relevant information found in the uploaded documents.")
            status.update(label="❌ No relevant content found", state="error")
        else:
            st.markdown(
                """
                <style>
                .search-result {
                    margin: 10px 0;
                    padding: 10px;
                    border-radius: 4px;
                    background-color: #f0f2f6;
                }
                .search-result summary {
                    cursor: pointer;
                    color: #0f52ba;
                    font-weight: 500;
                }
                .search-result summary:hover {
                    color: #1e90ff;
                }
                .metadata {
                    font-size: 0.9em;
                    color: #666;
                    font-style: italic;
                }
                </style>
            """,
                unsafe_allow_html=True,
            )

            st.write("Found relevant sections:")
            for chunk in context.split("\n\n"):
                # Split into text and metadata parts
                parts = chunk.split("\n")
                text = parts[0]
                metadata = {
                    line.split(": ")[0]: line.split(": ")[1]
                    for line in parts[1:]
                    if ": " in line
                }

                source = metadata.get("Source", "Unknown source")
                title = metadata.get("Title", "Untitled section")

                st.markdown(
                    f"""
                    <div class="search-result">
                        <details>
                            <summary>{source}</summary>
                            <div class="metadata">Section: {title}</div>
                            <div style="margin-top: 8px;">{text}</div>
                        </details>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            
            status.update(label="✅ Found relevant content", state="complete")

    # Display assistant response
    if context.strip():
        with st.chat_message("assistant"):
            # Get model response with streaming
            response = get_chat_response(st.session_state.messages, context)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        # Add a message indicating no relevant content was found
        no_content_response = "I couldn't find any relevant information in the uploaded documents to answer your question. Please try rephrasing your question or upload additional documents that might contain the information you're looking for."
        
        with st.chat_message("assistant"):
            st.markdown(no_content_response)
        
        st.session_state.messages.append({"role": "assistant", "content": no_content_response})

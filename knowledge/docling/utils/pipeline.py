"""
Document processing pipeline for dynamic upload and ingestion.

This module provides utilities to process documents through the Docling pipeline:
- Convert documents with DocumentConverter
- Chunk with HybridChunker
- Embed and store in LanceDB with OpenAI embeddings
"""

import os
from typing import Dict, List, Optional
from pathlib import Path

import lancedb
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from utils.tokenizer import OpenAITokenizerWrapper


# Schema definitions (must match existing schema)
class ChunkMetadata(LanceModel):
    """
    Metadata schema for chunks.
    Fields must be in alphabetical order (Pydantic requirement).
    """
    filename: str | None
    page_numbers: List[int] | None
    title: str | None


class Chunks(LanceModel):
    """Main schema for document chunks with embeddings."""
    text: str
    vector: Vector(1536)  # OpenAI text-embedding-3-large dimension
    metadata: ChunkMetadata


def get_or_create_table(db_path: str = "data/lancedb", table_name: str = "docling"):
    """
    Get or create the LanceDB table with the correct schema.
    
    Args:
        db_path: Path to the LanceDB database
        table_name: Name of the table
        
    Returns:
        LanceDB table object
    """
    # Ensure database directory exists
    os.makedirs(db_path, exist_ok=True)
    
    # Connect to database
    db = lancedb.connect(db_path)
    
    # Check if table exists
    try:
        table = db.open_table(table_name)
        return table
    except (FileNotFoundError, ValueError):
        # Table doesn't exist, create it
        func = get_registry().get("openai").create(name="text-embedding-3-large")
        
        # Update schema with proper embedding function
        class ChunksWithEmbedding(LanceModel):
            text: str = func.SourceField()
            vector: Vector(func.ndims()) = func.VectorField()  # type: ignore
            metadata: ChunkMetadata
        
        # Create empty table with schema
        table = db.create_table(table_name, schema=ChunksWithEmbedding, mode="create")
        return table


def process_documents(file_paths: List[str], db_path: str = "data/lancedb", table_name: str = "docling") -> Dict:
    """
    Process a list of documents through the complete pipeline.
    
    Args:
        file_paths: List of local file paths to process
        db_path: Path to the LanceDB database
        table_name: Name of the table to store chunks
        
    Returns:
        Dict with processing statistics:
        {
            "files_processed": int,
            "total_chunks": int,
            "per_file_stats": List[Dict],
            "failed_files": List[str]
        }
    """
    # Initialize components
    converter = DocumentConverter()
    tokenizer = OpenAITokenizerWrapper()
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=8191,  # text-embedding-3-large's maximum context length
        merge_peers=True,
    )
    
    # Get or create table
    table = get_or_create_table(db_path, table_name)
    
    # Initialize statistics
    stats = {
        "files_processed": 0,
        "total_chunks": 0,
        "per_file_stats": [],
        "failed_files": []
    }
    
    for file_path in file_paths:
        try:
            # Convert document
            result = converter.convert(file_path)
            
            if not result.document:
                stats["failed_files"].append(file_path)
                continue
            
            # Apply chunking
            chunk_iter = chunker.chunk(dl_doc=result.document)
            chunks = list(chunk_iter)
            
            if not chunks:
                stats["failed_files"].append(file_path)
                continue
            
            # Prepare chunks for embedding
            processed_chunks = []
            for chunk in chunks:
                processed_chunks.append({
                    "text": chunk.text,
                    "metadata": {
                        "filename": chunk.meta.origin.filename or Path(file_path).name,
                        "page_numbers": [
                            page_no
                            for page_no in sorted(
                                set(
                                    prov.page_no
                                    for item in chunk.meta.doc_items
                                    for prov in item.prov
                                )
                            )
                        ] or None,
                        "title": chunk.meta.headings[0] if chunk.meta.headings else None,
                    },
                })
            
            # Add chunks to table (automatically embeds)
            table.add(processed_chunks)
            
            # Update statistics
            file_stats = {
                "filename": Path(file_path).name,
                "chunks": len(processed_chunks),
                "status": "success"
            }
            stats["per_file_stats"].append(file_stats)
            stats["files_processed"] += 1
            stats["total_chunks"] += len(processed_chunks)
            
        except Exception as e:
            stats["failed_files"].append(file_path)
            file_stats = {
                "filename": Path(file_path).name,
                "chunks": 0,
                "status": f"failed: {str(e)[:100]}"
            }
            stats["per_file_stats"].append(file_stats)
    
    return stats


def get_table_stats(db_path: str = "data/lancedb", table_name: str = "docling") -> Dict:
    """
    Get statistics about the vector store table.
    
    Args:
        db_path: Path to the LanceDB database
        table_name: Name of the table
        
    Returns:
        Dict with table statistics:
        {
            "total_rows": int,
            "unique_files": List[str]
        }
    """
    try:
        table = get_or_create_table(db_path, table_name)
        
        # Get total row count
        total_rows = table.count_rows()
        
        # Get unique filenames
        df = table.to_pandas()
        if not df.empty:
            unique_files = df["metadata"].apply(lambda x: x.get("filename")).dropna().unique().tolist()
        else:
            unique_files = []
        
        return {
            "total_rows": total_rows,
            "unique_files": unique_files
        }
    
    except Exception:
        # Table doesn't exist or other error
        return {
            "total_rows": 0,
            "unique_files": []
        }
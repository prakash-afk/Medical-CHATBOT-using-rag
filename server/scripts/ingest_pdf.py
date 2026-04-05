import asyncio
import sys
import uuid
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from docs.vectorstore import describe_index_stats, load_vectorStore


class LocalUploadFile:
    def __init__(self, path: Path):
        self.path = path
        self.filename = path.name
        self.file = path.open("rb")

    def close(self) -> None:
        self.file.close()


async def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_pdf.py <pdf_path> [role]")
        return 1

    pdf_path = Path(sys.argv[1]).expanduser().resolve()
    role = sys.argv[2] if len(sys.argv) > 2 else "admin"

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return 1

    upload_file = LocalUploadFile(pdf_path)
    doc_id = str(uuid.uuid4())

    try:
        result = await load_vectorStore([upload_file], role=role, doc_id=doc_id)
        stats = describe_index_stats()
    finally:
        upload_file.close()

    print("Ingestion complete")
    print(f"doc_id: {result['doc_id']}")
    print(f"files_uploaded: {result['file_count']}")
    print(f"chunks_uploaded: {result['chunk_count']}")
    print(f"index_name: {result['index_name']}")
    print(f"vector_count: {stats.get('total_vector_count')}")
    print(f"namespaces: {stats.get('namespaces', {})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

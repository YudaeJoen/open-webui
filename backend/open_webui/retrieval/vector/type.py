try:
    from enum import StrEnum
except ImportError:
    # Python < 3.11 compatibility
    from enum import Enum
    class StrEnum(str, Enum):
        pass


class VectorType(StrEnum):
    MILVUS = 'milvus'
    MARIADB_VECTOR = 'mariadb-vector'
    QDRANT = 'qdrant'
    CHROMA = 'chroma'
    PINECONE = 'pinecone'
    ELASTICSEARCH = 'elasticsearch'
    OPENSEARCH = 'opensearch'
    PGVECTOR = 'pgvector'
    ORACLE23AI = 'oracle23ai'
    S3VECTOR = 's3vector'
    WEAVIATE = 'weaviate'
    OPENGAUSS = 'opengauss'
    VALKEY = 'valkey'

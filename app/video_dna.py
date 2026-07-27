from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class DNAResult:
    algorithm: str
    sample_count: int
    signature: str
    compact_signature: str

    def to_json(self) -> str:
        return json.dumps({
            "algorithm": self.algorithm,
            "sample_count": self.sample_count,
            "signature": self.signature,
            "compact_signature": self.compact_signature,
        }, ensure_ascii=False)


def _file_sample(path: Path, offset: int, size: int = 131072) -> bytes:
    with path.open("rb") as stream:
        stream.seek(max(0, offset))
        return stream.read(size)


def build_file_dna(filepath: str, sample_count: int = 24) -> DNAResult:
    """
    Empreinte rapide et locale basée sur plusieurs zones réparties dans le fichier.
    Elle sert à reconnaître les copies exactes ou quasi identiques sans relancer l'IA.
    """
    path = Path(filepath)
    stat = path.stat()
    size = stat.st_size
    if size <= 0:
        raise ValueError("Fichier vide")

    sample_count = max(6, min(100, int(sample_count)))
    digest = hashlib.sha256()
    compact_parts = []

    for index in range(sample_count):
        ratio = index / max(1, sample_count - 1)
        offset = int(max(0, size - 131072) * ratio)
        block = _file_sample(path, offset)
        block_hash = hashlib.blake2b(block, digest_size=16).digest()
        digest.update(index.to_bytes(2, "big"))
        digest.update(offset.to_bytes(8, "big"))
        digest.update(block_hash)
        compact_parts.append(block_hash.hex()[:8])

    digest.update(size.to_bytes(8, "big"))

    return DNAResult(
        algorithm="plexai-file-dna-v1",
        sample_count=sample_count,
        signature=digest.hexdigest(),
        compact_signature="-".join(compact_parts),
    )


def similarity(signature_a: str, signature_b: str) -> float:
    if not signature_a or not signature_b:
        return 0.0
    if signature_a == signature_b:
        return 1.0

    a = signature_a.split("-")
    b = signature_b.split("-")
    if len(a) < 2 or len(b) < 2:
        return 0.0

    limit = min(len(a), len(b))
    matches = sum(1 for index in range(limit) if a[index] == b[index])
    return matches / max(len(a), len(b))

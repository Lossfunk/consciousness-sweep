"""Explicit offline text-context estimates; never a claim of provider identity."""
import base64
from functools import lru_cache
import hashlib
import importlib.metadata
from pathlib import Path

METHOD = 'local-openai-text-v1'
VERSION = '0.14.0'
OVERHEAD_TOKENS = 32768
ASSETS = {
    'o200k_base': '446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d',
    'cl100k_base': '223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7',
}
# Plain-text patterns from the pinned public tiktoken implementation. Source
# strings resembling special tokens are counted literally via encode_ordinary.
PATTERNS = {'o200k_base': "[^\\r\\n\\p{L}\\p{N}]?[\\p{Lu}\\p{Lt}\\p{Lm}\\p{Lo}\\p{M}]*[\\p{Ll}\\p{Lm}\\p{Lo}\\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?|[^\\r\\n\\p{L}\\p{N}]?[\\p{Lu}\\p{Lt}\\p{Lm}\\p{Lo}\\p{M}]+[\\p{Ll}\\p{Lm}\\p{Lo}\\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?|\\p{N}{1,3}| ?[^\\s\\p{L}\\p{N}]+[\\r\\n/]*|\\s*[\\r\\n]+|\\s+(?!\\S)|\\s+", 'cl100k_base': "'(?i:[sdmt]|ll|ve|re)|[^\\r\\n\\p{L}\\p{N}]?+\\p{L}++|\\p{N}{1,3}+| ?[^\\s\\p{L}\\p{N}]++[\\r\\n]*+|\\s++$|\\s*[\\r\\n]|\\s+(?!\\S)|\\s"}


class CountingUnavailable(ValueError):
    pass


@lru_cache(maxsize=2)
def _encoder(name, raw):
    import tiktoken
    ranks = {}
    for line in raw.splitlines():
        token, rank = line.split()
        ranks[base64.b64decode(token, validate=True)] = int(rank)
    if len(ranks) != (199998 if name == 'o200k_base' else 100256):
        raise CountingUnavailable('Pinned token vocabulary has unexpected ranks')
    return tiktoken.Encoding(name=name, pat_str=PATTERNS[name], mergeable_ranks=ranks, special_tokens={})


def measure(profile, prompt, schema_text, base_instructions=''):
    try:
        version = importlib.metadata.version('tiktoken')
    except importlib.metadata.PackageNotFoundError:
        raise CountingUnavailable('Local context accounting requires bootstrap with the pinned tokenizer dependency')
    if version != VERSION:
        raise CountingUnavailable('Local context accounting requires tiktoken==' + VERSION)
    import tiktoken
    try:
        mapped = tiktoken.model.encoding_name_for_model(profile['model'])
    except KeyError:
        mapped = None  # Never pick an encoding by guessing a model alias.
    if mapped is not None and mapped not in {*ASSETS, 'o200k_harmony'}:
        raise CountingUnavailable('Known model encoding is outside this explicitly selected local text strategy')
    parts = {'prompt':prompt, 'schema':schema_text, 'operational_base':base_instructions}
    counts = {}
    for name, expected in ASSETS.items():
        path = Path(__file__).with_name(name + '.tiktoken')
        try:
            raw = path.read_bytes()
        except OSError:
            raise CountingUnavailable('Pinned local token vocabulary is unavailable: ' + name)
        if hashlib.sha256(raw).hexdigest() != expected:
            raise CountingUnavailable('Pinned local token vocabulary hash differs: ' + name)
        enc = _encoder(name, raw)
        counts[name] = {key:len(enc.encode_ordinary(text)) for key,text in parts.items()}
    text_bound = max(sum(value.values()) for value in counts.values())
    return {'method':METHOD, 'library':'tiktoken', 'library_version':version,
        'vocabulary_sha256':dict(ASSETS), 'component_counts':counts,
        'text_token_estimate':text_bound, 'context_overhead_reserve_tokens':OVERHEAD_TOKENS,
        'context_input_token_estimate':text_bound + OVERHEAD_TOKENS,
        'model':profile['model'], 'library_model_encoding':mapped,
        'model_tokenizer_verified':False, 'provider_framing_verified':False,
        'basis':'Explicit local estimate: maximum of two pinned text codecs plus fixed headroom; no provider-exact count or context-capacity claim'}

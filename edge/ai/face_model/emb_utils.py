import json
import numpy as np

def emb_to_json(emb: np.ndarray) -> str:
    return json.dumps(emb.astype(float).tolist())

def json_to_emb(s: str) -> np.ndarray:
    return np.array(json.loads(s), dtype=np.float32)

def l2_normalize(v: np.ndarray) -> np.ndarray:
    return v / (np.linalg.norm(v) + 1e-9)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    a = l2_normalize(a)
    b = l2_normalize(b)
    return float(np.dot(a, b))
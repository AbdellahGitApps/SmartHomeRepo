import numpy as np
import onnxruntime as ort
from app.core.config import FACE_ONNX_PATH
from .emb_utils import l2_normalize

class FaceEmbedder:
    def __init__(self):
        if not FACE_ONNX_PATH.exists():
            raise FileNotFoundError(f"Model not found: {FACE_ONNX_PATH}")

        self.session = ort.InferenceSession(str(FACE_ONNX_PATH), providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def embed(self, face_nhwc: np.ndarray) -> np.ndarray:
        out = self.session.run([self.output_name], {self.input_name: face_nhwc})[0]
        emb = out[0].astype(np.float32)
        return l2_normalize(emb)
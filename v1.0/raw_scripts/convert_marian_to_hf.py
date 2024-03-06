import argparse

from pathlib import Path
from transformers.models.marian.convert_marian_to_pytorch import convert


argparser = argparse.ArgumentParser('Convert Marian NMT models to pyTorch')
argparser.add_argument('--model-path', action="store", required=True)
argparser.add_argument('--dest-path', action="store", required=True)
args = argparser.parse_args()


Path(args.dest_path).mkdir(parents=True, exist_ok=True)
convert(Path(args.model_path), Path(args.dest_path))
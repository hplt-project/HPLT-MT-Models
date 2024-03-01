from huggingface_hub import HfApi
import os
import pandas as pd

# work on OPUS and HPLT separately
# add the readme template with placeholders
# read tsv file and extract lang id pairs in set
# iterate through set and after filtering start putting the values (for both ntrex and flores)
# once readme is created, save it and then upload the models by going to that path

readme_template = """---
language:
  - {src}
  - {trg_lang}
tags:
- translation
license: cc-by-4.0
---

### Translation model for {src}-{trg} OPUS_HPLT v1.0

This repository contains the model weights for translation models trained with Marian for HPLT project. For usage instructions, evaluation scripts, and inference scripts, please refer to the [HPLT-MT-Models v1.0](https://github.com/hplt-project/HPLT-MT-Models/tree/main/v1.0) GitHub repository.

* Source language: {src}
* Target language: {trg}
* Dataset: All of OPUS including HPLT
* Model: transformer-base
* Tokenizer: SentencePiece (Unigram)
* Cleaning: We use OpusCleaner for cleaning the corpus. Details about rules used can be found in the filter files in [Github](https://github.com/hplt-project/HPLT-MT-Models/tree/main/v1.0/data/{langpair}/raw/v2) 

To run inference with Marian, refer to the [Inference/Decoding/Translation](https://github.com/hplt-project/HPLT-MT-Models/tree/main/v1.0#inferencedecodingtranslation) section of our GitHub repository.


## Benchmarks

| testset                                | BLEU | chr-F | comet |
| -------------------------------------- | ---- | ----- | ----- |
| flores200     | {flores[0]} | {flores[1]}  | {flores[2]}  |
| ntrex | {ntrex[0]}   | {ntrex[1]}  | {ntrex[2]}  |
"""

results = pd.read_csv("./eval.tsv", sep="\t")

for pair in results["pair"].unique().tolist()[-10:-8]:
    src, trg = pair.split("-")

    if os.path.exists(f"/model/directory/check/models-15-feb/{src}-{trg}/"):
        langpair = f"{src}-{trg}"
    else:
        langpair = f"{trg}-{src}"

    if langpair == "en-zh_hant":  # zh_hant isn't a valid ISO code for HF
        trg_lang = "zh"

    # extract benchmark scores
    flores = results.loc[(results["train"]=="opus_hplt") &
                        (results["test"]=="flores") & 
                        (results["pair"]==pair), 
                        ["BLEU", "ChrF", "COMET"]].values.T.flatten()

    ntrex = results.loc[(results["train"]=="opus_hplt") &
                        (results["test"]=="ntrex") & 
                        (results["pair"]==pair), 
                        ["BLEU", "ChrF", "COMET"]].values.T.flatten()
    
    final_readme = readme_template.format(src=src, trg=trg, flores=flores, ntrex=ntrex, langpair=langpair, trg_lang=trg_lang)

    with open("readme_model.md", "w") as f:
        f.write(final_readme)

    api = HfApi()

    api.create_repo(
        repo_id=f"HPLT/translate-{src}-{trg}-v1.0-hplt_opus",
        repo_type="model",
    )

    api.upload_file(
        path_or_fileobj="readme_model.md",
        path_in_repo="README.md",
        repo_id=f"HPLT/translate-{src}-{trg}-v1.0-hplt_opus",
        repo_type="model",
    )

    api.upload_file(
        path_or_fileobj=f"/path/to/tokenizer/{langpair}/simple/v2/s.generate_vocab.{langpair}/output/model.{langpair}.spm",
        path_in_repo=f"model.{src}-{trg}.spm",
        repo_id=f"HPLT/translate-{src}-{trg}-v1.0-hplt_opus",
        repo_type="model",
    )

    api.upload_file(
        path_or_fileobj=f"/path/to/model/{langpair}/simple/v2/s.train_model.{src}-{trg}/output/model.npz.best-chrf.npz",
        path_in_repo="model.npz.best-chrf.npz",
        repo_id=f"HPLT/translate-{src}-{trg}-v1.0-hplt_opus",
        repo_type="model",
    )

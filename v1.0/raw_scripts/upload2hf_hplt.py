from huggingface_hub import HfApi
import os
import pandas as pd

# work on OPUS and HPLT separately
# add the readme template with placeholders
# read tsv file and extract lang id pairs in set
# iterate through set and after filtering start putting the values (for both ntrex and flores)
# once readme is created, save it and then upload the models by going to that path

code_map = {
    "ar" : "Arabic",
    "bs" : "Bosnian",
    "ca" : "Catalan",
    "en" : "English",
    "et" : "Estonian",
    "eu" : "Basque",
    "fi" : "Finnish",
    "ga" : "Irish",
    "gl" : "Galician",
    "hi" : "Hindi",
    "hr" : "Croatian",
    "is" : "Icelandic",
    "mt" : "Maltese",
    "nn" : "Norwegian",
    "sq" : "Albanian",
    "sw" : "Swahili",
    "zh_hant" : "Traditional Chinese",
}

readme_template = """---
language:
  - {src_lang}
  - {trg_lang}
tags:
- translation
license: cc-by-4.0
---

### HPLT MT release v1.0

This repository contains the translation model for {src}-{trg} trained with HPLT data only. For usage instructions, evaluation scripts, and inference scripts, please refer to the [HPLT-MT-Models v1.0](https://github.com/hplt-project/HPLT-MT-Models/tree/main/v1.0) GitHub repository.

### Model Info

* Source language: {src_name}
* Target language: {trg_name}
* Data: HPLT data only
* Model architecture: Transformer-base
* Tokenizer: SentencePiece (Unigram)
* Cleaning: We used OpusCleaner with a set of basic rules. Details can be found in the filter files in [Github](https://github.com/hplt-project/HPLT-MT-Models/tree/main/v1.0/data/{langpair}/raw/v0)

You can also read our deliverable report [here](https://hplt-project.org/HPLT_D5_1___Translation_models_for_select_language_pairs.pdf) for more details.

### Usage
{placeholder}

The model has been trained with Marian. To run inference, refer to the [Inference/Decoding/Translation](https://github.com/hplt-project/HPLT-MT-Models/tree/main/v1.0#inferencedecodingtranslation) section of our GitHub repository.

The model can be used with the Hugging Face framework if the weights are converted to the Hugging Face format. We might provide this in the future; contributions are also welcome.

## Benchmarks

| testset                                | BLEU | chrF++ | COMET22 |
| -------------------------------------- | ---- | ----- | ----- |
| flores200     | {flores[0]} | {flores[1]}  | {flores[2]}  |
| ntrex | {ntrex[0]}   | {ntrex[1]}  | {ntrex[2]}  |

### Acknowledgements

This project has received funding from the European Union's Horizon Europe research and innovation programme under grant agreement No 101070350 and from UK Research and Innovation (UKRI) under the UK government's Horizon Europe funding guarantee [grant number 10052546]

Brought to you by researchers from the University of Edinburgh, Charles University in Prague, and the whole HPLT consortium.
"""

results = pd.read_csv("./eval.tsv", sep="\t")

for pair in results["pair"].unique().tolist():
    src, trg = pair.split("-")

    if os.path.exists(f"/fs/lofn0/HPLT/models-15-feb/{src}-{trg}/"):
        langpair = f"{src}-{trg}"
    else:
        langpair = f"{trg}-{src}"

    if "zh_hant" in langpair:
        if src == "zh_hant":
            src_lang = "zh"
            trg_lang = trg
            placeholder = "**Note** that for quality considerations, we recommend using `" + f"[HPLT/translate-{src}-{trg}-v1.0-hplt_opus](https://huggingface.co/HPLT/translate-{src}-{trg}-v1.0-hplt_opus)" + "` instead of this model."
        else:
            src_lang = src
            trg_lang = "zh"
            placeholder = ""
    else:
        src_lang = src
        trg_lang = trg
        placeholder = "**Note** that for quality considerations, we recommend using " + f"[HPLT/translate-{src}-{trg}-v1.0-hplt_opus](https://huggingface.co/HPLT/translate-{src}-{trg}-v1.0-hplt_opus)" + " instead of this model."

    # extract benchmark scores
    flores = results.loc[(results["train"]=="hplt") &
                        (results["test"]=="flores") & 
                        (results["pair"]==pair), 
                        ["BLEU", "ChrF", "COMET"]].values.T.flatten()

    ntrex = results.loc[(results["train"]=="hplt") &
                        (results["test"]=="ntrex") & 
                        (results["pair"]==pair), 
                        ["BLEU", "ChrF", "COMET"]].values.T.flatten()

    final_readme = readme_template.format(src=src, trg=trg, flores=flores, ntrex=ntrex, langpair=langpair, placeholder=placeholder, src_lang=src_lang, trg_lang=trg_lang, src_name=code_map[src], trg_name=code_map[trg])

    with open("temp_readme_model.md", "w") as f:
        f.write(final_readme)

    api = HfApi()

    api.create_repo(
        repo_id=f"HPLT/translate-{src}-{trg}-v1.0-hplt",
        repo_type="model",
        exist_ok=True
    )

    api.upload_file(
        path_or_fileobj="temp_readme_model.md",
        path_in_repo="README.md",
        repo_id=f"HPLT/translate-{src}-{trg}-v1.0-hplt",
        repo_type="model",
        commit_message="update README"
    )

    api.upload_file(
        path_or_fileobj=f"/path/to/tokenizer/{langpair}/simple/v0/s.generate_vocab.{langpair}/output/model.{langpair}.spm",
        path_in_repo=f"model.{src}-{trg}.spm",
        repo_id=f"HPLT/translate-{src}-{trg}-v1.0-hplt",
        repo_type="model",
    )

    api.upload_file(
        path_or_fileobj=f"/path/to/model/{langpair}/simple/v0/s.train_model.{src}-{trg}/output/model.npz.best-chrf.npz",
        path_in_repo="model.npz.best-chrf.npz",
        repo_id=f"HPLT/translate-{src}-{trg}-v1.0-hplt",
        repo_type="model",
    )

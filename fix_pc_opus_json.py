import os
import json

import pathlib

CATEGORIES = {
  "categories": [
    {
      "name": "clean"
    },
    {
      "name": "medium"
    },
    {
      "name": "dirty"
    }
  ],
  "mapping": {
    "clean": [
    ]
  }
}

lang_pairs = ["ar-en", "ca-en", "en-et", "en-eu", "en-fi", "en-ga", "en-zh_TW"]

for lang_pair in lang_pairs:
    lang1, lang2 = lang_pair.split("-")
    if lang_pair == "en-zh_TW":
        read_path = "../data_filtering/data/train-parts/en-zh_hant/"
    else:
        read_path = "../data_filtering/data/train-parts/" + lang_pair + "/"
    lang1_gzs = [f for f in os.listdir(read_path) if f.endswith(".{}.{}.gz".format(lang_pair, lang1))]
    lang2_gzs = [f for f in os.listdir(read_path) if f.endswith(".{}.{}.gz".format(lang_pair, lang2))]
    lang1_prefixes = sorted([f.replace(".{}.gz".format(lang1), "") for f in lang1_gzs])
    lang2_prefixes = sorted([f.replace(".{}.gz".format(lang2), "") for f in lang2_gzs])
    assert lang1_prefixes == lang2_prefixes
    if lang_pair == "en-zh_TW":
        lang1_prefixes = [f.replace("zh_TW", "zh_hant") for f in lang1_prefixes]
        lang_pair = "en-zh_hant"
        lang2 = "zh_hant"

    write_paths = ["./v1.0/data/{}/raw/v1/".format(lang_pair), "./v1.0/data/{}/raw/v2/".format(lang_pair)]

    for write_path in write_paths:
        print(write_path)
        category_data = CATEGORIES.copy()
        category_data["mapping"]["clean"] = lang1_prefixes
        if "/v2/" in write_path:
            category_data["mapping"]["clean"].append("HPLT-v1.1.{}".format(lang_pair))
        with open(write_path + "categories.json", "w") as f:
            json.dump(category_data, f, indent=2)
        
        for lang1_prefix in lang1_prefixes:
            with open(write_path + "OPUS.{}.filters.json".format(lang_pair)) as f:
                filter_data = json.load(f)
                filter_data["files"] = ["{}.{}.gz".format(lang1_prefix, lang1),
                                        "{}.{}.gz".format(lang1_prefix, lang2)]
            with open(write_path + "{}.filters.json".format(lang1_prefix), "w") as f:
                json.dump(filter_data, f, indent=2)

            
        opus_name = write_path + "OPUS.{}.filters.json".format(lang_pair)
        if os.path.exists(opus_name):
            os.remove(opus_name)
        else:
            pass
        
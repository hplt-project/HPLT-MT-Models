# Created by P Chen to generate symlinks to test data so that the test file names match the HPLT language codes.


import os

HPLT_PAIRS = [
    "ar-en",
    "bs-en",
    "ca-en",
    "et-en",
    "eu-en",
    "en-fi",
    "en-ga",
    "en-gl",
    "en-hi",
    "en-hr",
    "en-is",
    "en-mt",
    "en-nn",
    "en-sq",
    "en-sw",
    "en-zh_hant",
]

FLOERS_MAP = {
    "ar": "arb_Arab",
    "bs": "bos_Latn",
    "ca": "cat_Latn",
    "en": "eng_Latn",
    "et": "est_Latn",
    "eu": "eus_Latn",
    "fi": "fin_Latn",
    "ga": "gle_Latn",
    "gl": "glg_Latn",
    "hi": "hin_Deva",
    "hr": "hrv_Latn",
    "is": "isl_Latn",
    "mt": "mlt_Latn",
    "nn": "nno_Latn",
    "sq": "als_Latn",
    "sw": "swh_Latn",
    "zh_hant": "zho_Hant",
}

NTREX_MAP = {
    "ar": "arb",
    "bs": "bos",
    "ca": "cat",
    "en": "eng",
    "et": "est",
    "eu": "eus",
    "fi": "fin",
    "ga": "gle",
    "gl": "glg",
    "hi": "hin",
    "hr": "hrv",
    "is": "isl",
    "mt": "mlt",
    "nn": "nno",
    "sq": "sqi",
    "sw": "swa",
    "zh_hant": "zho-TW",
}


for lang in FLOERS_MAP:
    try:
        os.symlink(
            "/some/dir/to/flores200/{}.devtest".format(
                FLOERS_MAP[lang]
            ),
            "./test_data/flores200/{}.txt".format(lang),
        )
    except FileExistsError:
        pass

    if lang != "en":
        try:
            os.symlink(
                "/some/dir/to/ntrex/newstest2019-ref.{}.txt".format(
                    NTREX_MAP[lang]
                ),
                "./test_data/ntrex/{}.txt".format(lang),
            )
        except FileExistsError:
            pass
    else:
        try:
            os.symlink(
                "/some/dir/to/ntrex/newstest2019-src.{}.txt".format(
                    NTREX_MAP[lang]
                ),
                "./test_data/ntrex/{}.txt".format(lang),
            )
        except FileExistsError:
            pass

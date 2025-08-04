#!/usr/bin/env python

#
# Download the train, dev and test data
#

import argparse
import gzip
import io
import logging
import shutil
import subprocess
import sys
import tarfile
import wget
import zipfile

from urllib.error import HTTPError
from pathlib import Path

LOG = logging.getLogger(__name__)

# Map 2-letter codes to codes used by (flores, ntrex)
# Note that we could use the Python langcodes package, but we also
# need to know that (eg) Flores has als for Albanian, and ntrex has sqi
LANG_MAP = {
    "af" : ("afr_Latn", "afr"),
    "ar" : ("arb_Arab", "arb"),
    "az" : ("azj_Latn", "aze-Latn"),
    "be" : ("bel_Cyrl", "bel"),
    "bg" : ("bul_Cyrl", "bul"),
    "bn" : ("ben_Beng", "ben"),
    "bs" : ("bos_Latn", "bos"),
    "ca" : ("cat_Latn", "cat"),
    "cy" : ("cym_Latn", "cym"),
    "eo" : ("epo_Latn", None),
    "et" : ("est_Latn", "est"),
    "eu" : ("eus_Latn", "eus"),
    "fa" : ("pes_Arab", "fas"),
    "fi" : ("fin_Latn", "fin"),
    "ga" : ("gle_Latn", "gle"),
    "gl" : ("glg_Latn", "glg"),
    "gu" : ("guj_Gujr", "guj"),
    "he" : ("heb_Hebr", "heb"),
    "hi" : ("hin_Deva", "hin"),
    "hr" : ("hrv_Latn", "hrv"),
    "is" : ("isl_Latn", "isl"),
    "ja" : ("jpn_Jpan", "jpn"),
    "kk" : ("kaz_Cyrl", "kaz"),
    "kn" : ("kan_Knda", "kan"),
    "ko" : ("kor_Hang", "kor"),
    "lv" : ("lvs_Latn", "lav"),
    "lt" : ("lit_Latn", "lit"),
    "mk" : ("mkd_Cyrl", "mkd"),
    "ml" : ("mal_Mlym", "mal"),
    "mr" : ("mar_Deva", "mar"),
    "ms" : ("zsm_Latn", "msa"),
    "mt" : ("mlt_Latn", "mlt"),
    "nb" : ("nob_Latn", "nob"),
    "ne" : ("nep_Deva", "nep"),
    "nn" : ("nno_Latn", "nob"), # This is Bokmal, not Nynorsk
    "si" : ("sin_Sinh", "sin"),
    "sk" : ("slk_Latn", "slk"),
    "sl" : ("slv_Latn", "slv"),
    "sq" : ("als_Latn", "sqi"),
    "sr" : ("srp_Cyrl", "srp-Cyrl"),
    "sw" : ("swh_Latn", "swa"),
    "ta" : ("tam_Taml", "tam"),
    "te" : ("tel_Telu", "tel"),
    "th" : ("tha_Thai", "tha"),
    "tr" : ("tur_Latn", "tur"),
    "uk" : ("ukr_Cyrl", "ukr"),
    "ur" : ("urd_Arab", "urd"),
    "uz" : ("uzn_Latn", "uzb"),
    "vi" : ("vie_Latn", "vie"),
    "xh" : ("xho_Latn", "xho"),
#    "zh_hant" : ("zho_Hant","zho-TW"),
}


#FIXME: Error checking
def get_cache_dir():
    cache_dir = Path.home() / ".hplt_model_data_cache"
    cache_dir.mkdir(exist_ok = True)
    return cache_dir


def get_test_data(data_dir, pair):
    LOG.debug(f"Downloading dev/test data in {data_dir}")
    pair3_arr = [LANG_MAP.get(l) for l in pair.split("-")]
    assert all(l != None for l in pair3_arr)

    test_dir = data_dir / "test"
    test_dir.mkdir(exist_ok=True)
    get_flores_data(pair, "devtest", test_dir)
    if all(lang3[1] is not None for lang3 in pair3_arr):
        get_ntrex_data(pair, "devtest", test_dir)

    dev_dir = data_dir / "valid"
    dev_dir.mkdir(exist_ok=True)
    get_flores_data(pair, "dev", dev_dir)


def add_reverse_link(path):
    name = path.name
    components = name.split(".")
    pair = components[-2]
    rev_pair = "-".join(reversed(pair.split("-")))
    components[-2] = rev_pair
    rev_name = ".".join(components)
    rev_path = path.parent / rev_name
    if not rev_path.is_symlink():
        print(rev_path)
        rev_path.symlink_to(path)


def get_flores_data(pair2, segment, dest_dir):
    pair3_arr = [LANG_MAP.get(lang)[0] for lang in pair2.split("-")]

    flores_path = get_cache_dir() / "flores200_dataset.tar.gz"
    if not flores_path.exists():
        wget.download("https://tinyurl.com/flores200dataset", out=flores_path.as_posix())
    for i, lang3 in enumerate(pair3_arr):
        if lang3 == "nep_Deva":
            pair3_arr[i] = "npi_Deva"  # flores-200 uses a different language-code

    with tarfile.open(flores_path, "r:gz") as flores_tar:
        for mylang, flang in zip(pair2.split("-"), pair3_arr):
            flores_path = f"./flores200_dataset/{segment}/{flang}.{segment}"
            my_path = dest_dir / f"flores200.{segment}.{pair2}.{mylang}"
            with open(my_path, "w") as ofh:
                for line in flores_tar.extractfile(flores_path):
                    print(line.decode('utf-8'), file=ofh, end="")
            add_reverse_link(my_path)


def get_ntrex_data(pair2, segment, dest_dir):
    pair3_arr = [LANG_MAP.get(lang)[1] for lang in pair2.split("-")]

    ntrex_path = get_cache_dir() / "ntrex"
    if not ntrex_path.exists():
        cmd = f"git clone https://github.com/MicrosoftTranslator/NTREX.git {ntrex_path}"
        subprocess.call(cmd.split())

    ntrex_path = ntrex_path / "NTREX-128"
    for lang2, lang3 in zip(pair2.split("-"), pair3_arr):
        my_path = dest_dir / f"ntrex.{pair2}.{lang2}"
        shutil.copy(ntrex_path / f"newstest2019-ref.{lang3}.txt", my_path)
        add_reverse_link(my_path)


def get_train_data(data_dir, pair):
    LOG.debug(f"Downloading training data in {data_dir}")

    if not data_dir.is_dir():
        data_dir.mkdir(parents=True)
    data_download_dest = data_dir / Path(f"MultiHPLT_v2.0.{pair}.txt.zip")
    if not data_download_dest.exists():
        wget.download(
            f"https://object.pouta.csc.fi/OPUS-MultiHPLT/v2/moses/{pair}.txt.zip",
            out=str(data_download_dest)
        )
    with zipfile.ZipFile(data_download_dest, "r") as zip_fh:
        zip_fh.extractall(data_dir)

    file_prefix = "MultiHPLT_v2.0"
    for lang in pair.split("-"):
        infile = data_dir / Path(f"MultiHPLT.{pair}.{lang}")
        outfile = data_dir / Path(f"{file_prefix}.{pair}.{lang}.gz")
        with io.BufferedReader(infile.open("rb")) as in_fh, gzip.open(outfile, "wb") as out_fh:
            LOG.debug(f"Compressing file {infile}")
            out_fh.writelines(in_fh)
        infile.unlink()
    data_download_dest.unlink()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--list-languages", action="store_true", default=False, help="List the available languages and exit."
    )
    parser.add_argument(
        "--lp", "--langpairs", dest="langpairs", default=[], nargs="+",
        help = "Specify list of hyphenated pairs of language codes to download."
    )
    parser.add_argument("--data-dir", type=str, default=None, help="Root directory for downloading the data.")
    parser.add_argument("--no-train", action="store_true", default=False, help="Do not download training data.")
    return parser.parse_args()


def main(args):
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(name)s:  %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG
    )
    if args.list_languages:
        for lang in LANG_MAP.keys():
            print(lang)
        sys.exit()
    LOG.info(f"Downloading data for selected language pairs: {args.langpairs}")

    data_dir = Path(__file__).parent.resolve()
    if args.data_dir is not None:
        data_dir = Path(args.data_dir)

    unk_langs = [l for lp in args.langpairs for l in lp.split("-") if not l in LANG_MAP]
    if unk_langs != []:
        raise RuntimeError(f"The following languages are unknown: {unk_langs}")
    langpairs = args.langpairs

    for pair in langpairs:
        # sort the languages in the language pair
        pair = "-".join(sorted(pair.split("-")))
        pair_data_dir = data_dir / pair
        LOG.info(f"Downloading data for {pair} to {pair_data_dir}")
        if not pair_data_dir.is_dir():
            pair_data_dir.mkdir(parents=True)
        get_test_data(pair_data_dir, pair)
        if not args.no_train:
            get_train_data(pair_data_dir / Path("raw"), pair)


if __name__ == "__main__":
  main(parse_args())

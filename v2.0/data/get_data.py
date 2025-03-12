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


def get_test_data(data_dir, other_lang):
    LOG.debug(f"Downloading dev/test data in {data_dir}")
    lang3 = LANG_MAP.get(other_lang)
    assert(lang3 != None)
  
    test_dir = data_dir / "test"
    test_dir.mkdir(exist_ok=True)
    get_flores_data(other_lang, lang3[0], "devtest", data_dir.name, test_dir)
    if lang3[1] is not None:
        get_ntrex_data(other_lang, lang3[1], "devtest", data_dir.name, test_dir)
  
    dev_dir = data_dir / "valid"
    dev_dir.mkdir(exist_ok=True)
    get_flores_data(other_lang, lang3[0], "dev", data_dir.name, dev_dir)

  
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

  
def get_flores_data(lang2, lang3, segment, pair, dest_dir):
    flores_path = get_cache_dir() / "flores200_dataset.tar.gz"
    if not flores_path.exists():
        wget.download("https://tinyurl.com/flores200dataset", out=flores_path.as_posix())
    if lang3 == "nep_Deva":
        lang3 = "npi_Deva"  # flores-200 uses a different language-code

    with tarfile.open(flores_path, "r:gz") as flores_tar:
        for mylang,flang in ((lang2,lang3), ("en","eng_Latn")):
            flores_path = f"./flores200_dataset/{segment}/{flang}.{segment}"
            my_path = dest_dir / f"flores200.{segment }.{pair}.{mylang}"
            with open(my_path, "w") as ofh:
                for line in flores_tar.extractfile(flores_path):
                    print(line.decode('utf-8'), file=ofh, end="")
            add_reverse_link(my_path)
    
      
def get_ntrex_data(lang2, lang3, segment, pair, dest_dir):
    ntrex_path = get_cache_dir() / "ntrex"
    if not ntrex_path.exists():
        cmd = f"git clone https://github.com/MicrosoftTranslator/NTREX.git {ntrex_path}"
        subprocess.call(cmd.split())
    ntrex_path = ntrex_path /  "NTREX-128"
    ntrex_eng = dest_dir / f"ntrex.{pair}.en"
    shutil.copy(ntrex_path / "newstest2019-src.eng.txt", ntrex_eng)
    add_reverse_link(ntrex_eng)
    ntrex_for = dest_dir / f"ntrex.{pair}.{lang2}"
    shutil.copy(ntrex_path / f"newstest2019-ref.{lang3}.txt", ntrex_for)
    add_reverse_link(ntrex_for)
        
  
def get_train_data(data_dir, pair):
    LOG.debug(f"Downloading training data in {data_dir}")
    
    # v0 (HPLT v2 only)
    v0_data_dir = data_dir / Path("v0")
    if not v0_data_dir.is_dir():
        v0_data_dir.mkdir(parents=True)
    v0_data_download_dest = v0_data_dir / Path(f"HPLT_v2.0.{pair}.txt.zip")
    if not v0_data_download_dest.exists():
        wget.download(
            f"https://opus.nlpl.eu/legacy/download.php?f=HPLT/v2/moses/{pair}.txt.zip",
            out=str(v0_data_download_dest)
        )
    with zipfile.ZipFile(v0_data_download_dest, "r") as zip_fh:
        zip_fh.extractall(v0_data_dir)

    v0_file_prefix = "HPLT_v2.0"
    for lang in pair.split("-"):
        infile = v0_data_dir / Path(f"HPLT.{pair}.{lang}")
        outfile = v0_data_dir / Path(f"{v0_file_prefix}.{pair}.{lang}.gz")
        with io.BufferedReader(infile.open("rb")) as in_fh, gzip.open(outfile, "wb") as out_fh:
            LOG.debug(f"Compressing file {infile}")
            out_fh.writelines(in_fh)
        infile.unlink()
    v0_data_download_dest.unlink()

    # v1 (Tatoeba only)
    pair3 = "-".join([LANG_MAP[lang][0].split("_")[0] if lang in LANG_MAP else "eng" for lang in pair.split("-")])
    v1_data_dir = data_dir / Path("v1")
    if not v1_data_dir.is_dir():
        v1_data_dir.mkdir(parents=True)
    v1_data_download_dest = v1_data_dir / Path(f"{pair3}.tar")
    if not v1_data_download_dest.exists():
        LOG.debug(f"Trying to download {v1_data_download_dest}...")
        try:
            wget.download(
                f"https://object.pouta.csc.fi/Tatoeba-Challenge-v2023-09-26/{pair3}.tar",
                out=str(v1_data_download_dest)
            )
        except HTTPError as err:
            v1_data_dir.rmdir()
            return
    with tarfile.TarFile(v1_data_download_dest, "r") as tar_fh:
        tar_fh.extractall(v1_data_dir)

    v1_file_prefix = "tatoeba"
    for side, lang in zip(["src", "trg"], pair.split("-")):
        if lang in LANG_MAP:
            lang3 = LANG_MAP[lang][1]
        else:
            lang3 = "eng"
        infile = v1_data_dir / Path(f"data/release/v2023-09-26/{pair3}/train.{side}.gz")
        outfile = v1_data_dir / Path(f"{v1_file_prefix}.{pair}.{lang}.gz")
        shutil.copy(infile, outfile)
        infile.unlink()
    v1_data_download_dest.unlink()

    # v2 (HPLT v2 + Tatoeba)
    v2_data_dir = data_dir /Path("v2")
    if not v2_data_dir.is_dir():
        v2_data_dir.mkdir(parents=True)
    for lang in pair.split("-"):
        for data_dir, file_prefix in zip([v0_data_dir, v1_data_dir], [v0_file_prefix, v1_file_prefix]):
            infile = data_dir / Path(f"{file_prefix}.{pair}.{lang}.gz")
            outfile = v2_data_dir / Path(f"{file_prefix}.{pair}.{lang}.gz")
            outfile.hardlink_to(infile)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--list-languages", action="store_true", default=False, help="List the available languages and exit."
    )
    parser.add_argument(
        "-l", "--languages", default="all", nargs="+",
        help = "Specify list of non-English language codes to download. Defaults to 'all' to download all data."
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
    if "all" in args.languages:
        LOG.info("Downloading data for all languages")
    else:
        LOG.info(f"Downloading data for selected languages: {args.languages}")
 
    data_dir = Path(__file__).parent.resolve()
    if args.data_dir is not None:
        data_dir = Path(args.data_dir)
    if "all" in args.languages:
        languages = list(LANG_MAP.keys())
    else:
        unk_langs = [l for l in args.languages if not l in LANG_MAP]
        if unk_langs != []:
            raise RuntimeError(f"The following languages are unknown: {unk_langs}")
        languages = args.languages
    
    for language in languages:
        pair = "-".join(sorted(("en", language)))
        pair_data_dir = data_dir / pair
        LOG.info(f"Downloading data for {pair} in {pair_data_dir}")
        if not pair_data_dir.is_dir():
            pair_data_dir.mkdir(parents=True)
        get_test_data(pair_data_dir, language)
        if not args.no_train:
            get_train_data(pair_data_dir / Path("raw"), pair)


if __name__ == "__main__":
  main(parse_args())

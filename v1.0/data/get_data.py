#!/usr/bin/env python

#
# Download the train, dev and test data
#

import argparse
import logging
import shutil
import subprocess
import tarfile
import wget

from pathlib import Path

LOG = logging.getLogger(__name__)

# Map 2-letter codes to codes used by (flores, ntrex)
# Note that we could use the Python langcodes package, but we also
# need to know that (eg) Flores has als for Albanian, and ntrex has sqi
LANG_MAP = {
    "ar" : ("arb_Arab","arb"),
    "bs" : ("bos_Latn", "bos"),
    "ca" : ("cat_Latn", "cat"),
    "et" : ("est_Latn", "est"),
    "eu" : ("eus_Latn", "eus"),
    "fi" : ("fin_Latn", "fin"),
    "ga" : ("gle_Latn", "gle"),
    "gl" : ("glg_Latn","glg"),
    "hi" : ("hin_Deva", "hin"),
    "hr" : ("hrv_Latn", "hrv"),
    "is" : ("isl_Latn", "isl"),
    "mk" : ("mkd_Cyrl", "mkd"),
    "mt" : ("mlt_Latn", "mlt"),
    "nn" : ("nno_Latn", "nob"), # This is Bokmal, not Nynorsk
    "sq" : ("als_Latn","sqi"),
    "sr_cyrillic" : ("srp_Cyrl", "srp-Cyrl"),
    "sw" : ("swh_Latn","swa"),
    "zh_hant" : ("zho_Hant","zho-TW"),
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
    
    
  
def get_train_data(data_dir, ocd_path):
  LOG.debug(f"Downloading training data  in {data_dir}")
  cmd = f"{ocd_path} -d {data_dir}"
  subprocess.call(cmd.split())

def main():
  logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s:  %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
  parser = argparse.ArgumentParser()
  parser.add_argument("-l", "--languages", required = True, nargs="+", help = 
      "Specify list of non-English language codes to download. Set to 'all' to download all data")
  parser.add_argument("--no-train", action="store_true", default=False, help="Do not download training data")
  args = parser.parse_args()
  if "all" in args.languages:
    LOG.info("Downloading data for all languages")
  else:
    LOG.info(f"Downloading data for selected languages: {args.languages}")
 
  OCD_EXE = "opuscleaner-download"
  ocd_path = shutil.which(OCD_EXE)
  if ocd_path == None:
    raise RuntimeError("Unable to find the opuscleaner-download executable")
  else:
    LOG.info(f"Using {ocd_path} to download training data")
    
  data_dir = Path(__file__).parent 
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
      raise RuntimeError(f"Expected directory {pair_data_dir} not found")
    get_test_data(pair_data_dir, language)
    if not args.no_train:
      get_train_data(pair_data_dir, ocd_path)


if __name__ == "__main__":
  main()

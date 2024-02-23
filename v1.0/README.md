## First release of HPLT models

This directory contains scripts, configuration and logs for model training.  

### Model Download

Download the models from [HuggingFace](TBD), or following the links in (download.md)

### Model Usage

### Downloading Training, Development and Test data

The directory `data` contains the configuration for downloading the datasets used to train and evaluate the models. We use data from [Opus](https://opus.nlpl.eu/) and build models with and without the 
[HPLT](https://hplt-project.org/) data release (V1.1). For dev and test we use  [Flores200](https://github.com/facebookresearch/flores/blob/main/flores200/README.md) and [NTREX](https://github.com/MicrosoftTranslator/NTREX) datasets.

To download the data, first make sure that [OpusCleaner](https://github.com/hplt-project/OpusCleaner) is installed, 
then install the Python requirements in `data/requirements.txt`. To 
download data from selected languages, run the following from the `data` directory:
```
./get_data.py -l LANG1 LANG2 ...
```
providing the 2-letter language codes.
To download all data, use
```
./get_data.py -l all
```
Since the data download does not currently parallelise or cache, this will be slow.

### Training Models

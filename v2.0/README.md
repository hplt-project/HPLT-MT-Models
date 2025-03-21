## The second release of HPLT models (and the training pipeline!)

This directory contains scripts, configurations, and logs for model inference and training.  


### Using the Models: Inference/Decoding/Translation

We provide below an instruction on running translation with the [MarianNMT](https://github.com/marian-nmt/marian) toolkit.
However, it is also possible to use other toolkits if you convert the model weights to compatible formats, for example, Hugging Face.

Clone MarianNMT and compile the toolkit.
Note that you will need to compile with `-DUSE_SENTENCEPIECE=on` because our models use a SentencePiece vocabulary.
If you intend to run inference on CPU, please pass the `-DCOMPILE_CPU=on` flag as well.

```
git clone https://github.com/marian-nmt/marian.git
mkdir -p marian/build
cd marian/build
cmake .. -DUSE_SENTENCEPIECE=on
make -j8
```

To run translation, you should specify a path to the Marian decoder you just built, which should look like `your_path_to_marian/marian/build/marian-decoder`, and a path to the Marian configuration file that we supply in this repository `HPLT-MT-Models/v2.0/inference/inference_config.yml`.
Feel free to modify the configurations to suit your needs.
You should set the environment variable `CUDA_VISIBLE_DEVICES` to the GPU device(s) you want to use, e.g. `1,2,3,4`.
If you want to use CPU, please change the `--devices` option to `--cpu-threads` and pass a integer that is larger than `0`.

Please download the model and vocabulary files from [HPLT's MT model collection on Hugging Face](TODO) or https://data.statmt.org/hplt-models/translate/v2.0/.
Pass the model checkpoint and vocabulary files to the decoder.
Finally, specify a path to the input file and the output (hypothesis) file (or omit for translation from `stdin` to `stdout`). Putting it all together gives:

```
marian_decoder=# Path to marian-decoder executable
marian_config= # Path to inference_config.yml
gpu_devices=$(echo -ne "$CUDA_VISIBLE_DEVICES" | tr "," " ")
model_dir= # path where you checked out the model
model_checkpoint=${model_dir}/model.npz.best-chrf.npz
vocab_file=${model_dir}/model.${lang_pair}.spm # Insert correct language pair, e.g mt-en for Maltese-to-English

${marian_decoder} \
    --config ${marian_config} \
    --models ${model_checkpoint} \
    --vocabs ${vocab_file} ${vocab_file} \
    --devices ${gpu_devices} \
    --input ${input_source_filename} \ 
    --output ${output_hypothesis_filename}
```


### Evaluation

We provide example scripts to compute BLEU, chrF++, and COMET.
We recommend that you use [sacrebleu](https://github.com/mjpost/sacrebleu) to compute BLEU scores.
Specifically, you need to set a tokenization method: For the languages in our release, please use `13a`, except for Traditional Chinese, for which you should use `zh`.

The automatic evaluation using BLEU and chrF++ (using Python implementation of SacreBLEU) is also included in the OpusPocus training pipeline.
```
pip install --upgrade sacrebleu

tokenizer=13a # or replace with "zh"
sacrebleu --tokenize ${tokenizer} -m bleu -b ${output_hypothesis_filename} <${reference_filename}
```

Similarly, chrF++ scores can be computed as:
```
sacrebleu -m chrf --chrf-word-order 2 -b ${output_hypothesis_filename} <${reference_filename}
```

COMET scores can be obtained using with the following command. You need to specify a path to the COMET checkpoint you wish to use. For details please refer to the documentation of [COMET](https://github.com/Unbabel/COMET). You might need to have python3.9 to [get the right scores](https://github.com/Unbabel/COMET/issues/203).

```
pip install --upgrade unbabel-comet

comet-score \
    -s ${input_source_filename} \
    -t ${output_hypothesis_filename} \
    -r ${reference_filename} \
    --model some/path/wmt22-comet-da/checkpoints/model.ckpt \
    --quiet \
    --only_system
```

### Data for Training, Validation and Test

The directory `data` contains the configuration for downloading the datasets used to train and evaluate the models.
We use the [HPLT](https://hplt-project.org/) data release (v2.0) and data from [Tatoeba](https://github.com/Helsinki-NLP/Tatoeba-Challenge/tree/master/data) wherever available.
For dev and test we use  [Flores200](https://github.com/facebookresearch/flores/blob/main/flores200/README.md) and [NTREX](https://github.com/MicrosoftTranslator/NTREX) (if available) datasets.

For each language pair (e.g. en-ja), we create a subdirectory (e.g `data/en-ja/`), which contains the following directories with data:
- `v0/` ... contains the HPLT v2.0 dataset
- `v1/` ... contains the Tatoeba dataset
- `v2/` ... contains the links to the HPLT v2.0 and Tatoeba datasets
(NOTE: directories `v1/` and `v2/` are created only if the Tatoeba dataset for the given language pair is available.)

To download the data, install the Python requirements in `data/requirements.txt`. To 
download data from selected languages, run the following from the `data/` directory:
```
data/get_data.py -l LANG1 LANG2 ...
```
providing the 2-letter language codes.
To download all data, use
```
data/get_data.py -l all
```

Since the data download does not currently parallelise or cache, this will be slow.

To see the list of the supported languages, run the following command:
```
data/get_data.py --list-languages
```

### Training

The data preprocessing and model training pipelines use the [OpusPocus](https://github.com/hplt-project/OpusPocus) pipeline manager.
Before running the pipelines, checkout the OpusPocus submodule in `training/OpusPocus/` and add the submodule location to your PYTHONPATH:
```
export PYTHONPATH=/path/to/training/OpusPocus
```


You can then run the data preprocessing and model training pipelines using the `opuspocus_run_wrapper.py` (make sure that you successfully prepared the training/validation data using the previous step):
```
training/opuspocus_run_wrapper.py -l LANG --data-version VERSION --runner bash
```

or if you prefer using the SLURM HPC scheduler:
```
training/opuspocus_run_wrapper.py -l LANG --data-version VERSION --runner slurm --runner-options slurm_time=TIME slurm_other_options="--account=$ACCOUNT,--partition=$PARTITION,--mem=$MEM"
```
(NOTE: You can replace the `slurm_other_options` with the comma-separated SLURM options of your preference)

You can also execute the data preprocessing and model training pipelines separately:
```
training/opuspocus_run_wrapper.py -l LANG --data-version VERSION --runner RUNNER --preprocess-only
training/opuspocus_run_wrapper.py -l LANG --data-version VERSION --runner RUNNER --train-only
```

If needed, you can also set the location of your Marian NMT directory using `--marian-dir`.

### Acknowledgements

This project has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No 101070350 and from UK Research and Innovation (UKRI) under the UK government’s Horizon Europe funding guarantee [grant number 10052546]

### Licence
The models are licensed under CC-BY 4.0

## First release of HPLT models

This directory contains scripts, configuration and logs for model training.  

### Model Download and Usage

Download the models from [HuggingFace](TBD), or following the links in the [download page](download.md)

### Training, Development and Test data

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

### Training

### Inference/Decoding/Translation

We provide below an instruction on running translation with the [MarianNMT](https://github.com/marian-nmt/marian) toolkit. However, it is also possible to use other toolkits if you convert the model weights to compatible formats, for example, Hugging Face.

Clone MarianNMT and compile the toolkit. Note that you will need to compile with `-DUSE_SENTENCEPIECE=on` because our models use a SentencePiece vocabulary. If you intend to run inference on CPU, please pass the `-DCOMPILE_CPU=on` flag as well.

```
git clone https://github.com/marian-nmt/marian.git
mkdir -p marian/build
cd marian/build
cmake .. -DUSE_SENTENCEPIECE=on
make -j8
```

Specify a path to the Marian decoder you just built, which should look like `your_path_to_marian/marian/build/marian-decoder`, and a path to the Marian configuration file that we supply in this repository `HPLT-MT-Models/v1.0/inference/inference_config.yml`. Feel free to modify the configurations to suit your needs. You should set the environment variable `CUDA_VISIBLE_DEVICES` to the GPU device(s) you want to use, e.g. `1,2,3,4`. If you want to use CPU, please change the `--devices` option to `--cpu-threads` and pass a integer that is larger than `0`.

Please download the model and vocabulary files from [HPLT's Hugging Face page](https://huggingface.co/HPLT), or check the model weight table below for details. Pass the model checkpoint and vocabulary files to the decoder. Finally, specify a path to the input file and the output (hypothesis) file, and run the following command:

```
marian_decoder=/fs/lofn0/patrickchen/marian/build/marian-decoder
marian_config=/fs/lofn0/patrickchen/HPLT/evaluation/marian_config.yml
gpu_devices=$(echo -ne "$CUDA_VISIBLE_DEVICES" | tr "," " ")

${marian_decoder} \
    --config ${marian_config} \
    --models ${model_checkpoint} \
    --vocabs ${vocab_file} ${vocab_file} \
    --devices ${gpu_devices} \
    --input ${input_source_filename} \
    --output ${output_hypothesis_filename}
```

### Evaluation

We provide example scripts to compute BLEU, chrF++, and COMET. We recommend that you use [sacrebleu](https://github.com/mjpost/sacrebleu) to compute BLEU scores. Specifically, you need to set a tokenization method: For the languages in our release, please use `13a`, except for Traditional Chinese, for which you should use `zh`.
```
pip install --upgrade sacrebleu

tokenizer=13a # or replace with "zh"
sacrebleu --tokenize ${tokenizer} -m bleu -b ${output_hypothesis_filename} <${reference_filename}
```

Similarly, chrF++ scores can be computed as:
```
sacrebleu -m chrf --chrf-word-order 2 -b ${output_hypothesis_filename} <${reference_filename}
```

COMET scores can be obtained using with the following command. You need to specify a path to the COMET checkpoint you wish to use. For details please refer to the documentation of [COMET](https://github.com/Unbabel/COMET). Also, you might to have python3.9 to [get the right scores](https://github.com/Unbabel/COMET/issues/203).

```
pip install --upgrade unbabel-comet

comet-score \
    -s ${input_source_filename} \
    -t ${output_hypothesis_filename} \
    -r ${reference_filename} \
    --model some/path/wmt22-comet-da/checkpoints/model.ckpt \
    --quiet
```
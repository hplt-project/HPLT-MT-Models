#!/bin/bash
# Created by P Chen to run evaluation on all language pairs and test sets to generate eval.tsv

MODEL_DIR=/some/dir/to/models
TEST_DIR=./test_data
OUTPUT_DIR=./output

mkdir -p ./evaluated
TSV_FILE=./eval.tsv

declare -A TRAIN_SETS=(["v0"]="hplt" ["v1"]="opus" ["v2"]="opus_hplt")
declare -A TEST_SETS=(["ntrex"]="ntrex" ["flores200"]="flores")

get_tok() {
    if [[ "$1" == *"zh_han"* ]]; then
        echo -ne "zh"
    else
        echo -ne "13a"
    fi
}

get_bleu() {
    sacrebleu --tokenize $(get_tok $2) -m bleu -b $1 <$2
}

get_chrF() {
    sacrebleu --tokenize $(get_tok $2) -m chrf --chrf-word-order 2 -b $1 <$2
}

get_comet() {
    COMET_SCORE=$(comet-score -s $3 -t $2 -r $1 --model /some/dir/to/wmt22-comet-da/checkpoints/model.ckpt --batch_size 128 --quiet)
    echo ${COMET_SCORE##*:} | awk '{$1=$1};1'
}

if [ $(ls ./evaluated/ | wc -l) -eq "0" ]; then
    rm -f ${TSV_FILE}
    touch ${TSV_FILE}
    echo -ne "pair\ttrain\ttest\tBLEU\tChrF\tCOMET\n" >>${TSV_FILE}
fi

for LANG1 in ar bs ca et eu fi ga gl hi hr is mk mt nn sq sr sw zh_hant; do
    # assuming English-centric models
    LANG2=en
    # XX-en
    if [ ! -f ./evaluated/${LANG1}-${LANG2}.evaluated ]; then
        if [ -d ${MODEL_DIR}/${LANG1}-${LANG2} ] || [ -d ${MODEL_DIR}/${LANG2}-${LANG1} ]; then
            for VERSION in v0 v1 v2; do
                for TEST_SET in ntrex flores200; do
                    echo -ne "${LANG1}-${LANG2}" >>${TSV_FILE}
                    echo -ne "\t${TRAIN_SETS[${VERSION}]}" >>${TSV_FILE}
                    echo -ne "\t${TEST_SETS[${TEST_SET}]}" >>${TSV_FILE}
                    for FUNC in get_bleu get_chrF get_comet; do
                        SRC_FILE=${TEST_DIR}/${TEST_SET}/${LANG1}.txt
                        HYP_FILE=${OUTPUT_DIR}/${TEST_SET}.${LANG1}-${LANG2}.${VERSION}.txt
                        REF_FILE=${TEST_DIR}/${TEST_SET}/${LANG2}.txt

                        echo -ne "\t$(${FUNC} ${REF_FILE} ${HYP_FILE} ${SRC_FILE})" >>${TSV_FILE}
                    done
                    echo -ne "\n" >>${TSV_FILE}
                done
            done
            touch ./evaluated/${LANG1}-${LANG2}.evaluated
        fi
    fi

    # en-XX
    if [ ! -f ./evaluated/${LANG2}-${LANG1}.evaluated ]; then
        if [ -d ${MODEL_DIR}/${LANG2}-${LANG1} ] || [ -d ${MODEL_DIR}/${LANG1}-${LANG2} ]; then
            for VERSION in v0 v1 v2; do
                for TEST_SET in ntrex flores200; do
                    echo -ne "${LANG2}-${LANG1}\t" >>${TSV_FILE}
                    echo -ne "\t${TRAIN_SETS[${VERSION}]}" >>${TSV_FILE}
                    echo -ne "\t${TEST_SETS[${TEST_SET}]}" >>${TSV_FILE}
                    for FUNC in get_bleu get_chrF get_comet; do
                        SRC_FILE=${TEST_DIR}/${TEST_SET}/${LANG2}.txt
                        HYP_FILE=${OUTPUT_DIR}/${TEST_SET}.${LANG2}-${LANG1}.${VERSION}.txt
                        REF_FILE=${TEST_DIR}/${TEST_SET}/${LANG1}.txt

                        echo -ne "\t$(${FUNC} ${REF_FILE} ${HYP_FILE} ${SRC_FILE})" >>${TSV_FILE}
                    done
                    echo -ne "\n" >>${TSV_FILE}
                done
            done
            touch ./evaluated/${LANG2}-${LANG1}.evaluated
        fi
    fi
done

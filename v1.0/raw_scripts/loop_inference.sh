#!/bin/bash
# Created by P Chen to run inference on all language pairs and test sets

DEVICES=$(echo -ne "$1" | tr "," " ")

MARIAN_DECODER=/some/dir/to/marian/build/marian-decoder
MARIAN_CONFIG=/some/dir/to/marian_config.yml

MODEL_DIR=/some/dir/to/models
CKPT=model.npz.best-chrf.npz # using the best model according to chrF since it's the metric used for early stopping
TEST_DIR=./test_data
OUTPUT_DIR=./output
mkdir -p ${OUTPUT_DIR}

for LANG1 in ar bs ca et eu fi ga gl hi hr is mk mt nn sq sr sw zh_hant ; do
    # assuming English-centric models
    LANG2=en
    for VERSION in v0 v1 v2; do
        for TEST_SET in ntrex flores200; do
            if [ -d ${MODEL_DIR}/${LANG1}-${LANG2} ] || [ -d ${MODEL_DIR}/${LANG2}-${LANG1} ]; then
                if [ -d ${MODEL_DIR}/${LANG1}-${LANG2} ]; then
                    LANG_PAIR=${LANG1}-${LANG2}
                else
                    LANG_PAIR=${LANG2}-${LANG1}
                fi
                # assuming the same joint vocabulary for both directions
                VOCAB_FILE=${MODEL_DIR}/${LANG_PAIR}/simple/${VERSION}/s.generate_vocab.${LANG_PAIR}/output/model.${LANG_PAIR}.spm

                # LANG_1 -> LANG_2
                SRC_FILE=${TEST_DIR}/${TEST_SET}/${LANG1}.txt
                HYP_FILE=${OUTPUT_DIR}/${TEST_SET}.${LANG1}-${LANG2}.${VERSION}.txt
                REF_FILE=${TEST_DIR}/${TEST_SET}/${LANG2}.txt
                MODEL_LANG1_LANG2=${MODEL_DIR}/${LANG_PAIR}/simple/${VERSION}/s.train_model.${LANG1}-${LANG2}/output/${CKPT}

                if [ ! -f ${HYP_FILE} ]; then
                    echo "Working on ${HYP_FILE}."
                    ${MARIAN_DECODER} \
                        --config ${MARIAN_CONFIG} \
                        --models ${MODEL_LANG1_LANG2} \
                        --vocabs ${VOCAB_FILE} ${VOCAB_FILE} \
                        --devices ${DEVICES} \
                        --input ${SRC_FILE} \
                        --output ${HYP_FILE}
                else
                    echo "Skipping ${HYP_FILE} because it exists."
                fi

                # LANG_2 -> LANG_1
                SRC_FILE=${TEST_DIR}/${TEST_SET}/${LANG2}.txt
                HYP_FILE=${OUTPUT_DIR}/${TEST_SET}.${LANG2}-${LANG1}.${VERSION}.txt
                REF_FILE=${TEST_DIR}/${TEST_SET}/${LANG1}.txt
                MODEL_LANG2_LANG1=${MODEL_DIR}/${LANG_PAIR}/simple/${VERSION}/s.train_model.${LANG2}-${LANG1}/output/${CKPT}

                if [ ! -f ${HYP_FILE} ]; then
                    echo "Working on ${HYP_FILE}."
                    ${MARIAN_DECODER} \
                        --config ${MARIAN_CONFIG} \
                        --models ${MODEL_LANG2_LANG1} \
                        --vocabs ${VOCAB_FILE} ${VOCAB_FILE} \
                        --devices ${DEVICES} \
                        --input ${SRC_FILE} \
                        --output ${HYP_FILE}
                else
                    echo "Skipping ${HYP_FILE} because it exists."
                fi
            else
                echo "Skipping ${LANG1}<->${LANG2} because neither ${MODEL_DIR}/${LANG1}-${LANG2} nor ${MODEL_DIR}/${LANG2}-${LANG1} exists."
            fi
        done
    done
done

#!/bin/bash

src_dir=/fs/lofn0/HPLT/models-15-feb/
dest_dir=/home/bhaddow/data/HPLT-MT-Models/v1-release

mkdir -p $dest_dir

copy_model() {
    pair_dir=$1
    pair=$2
    v=$3
    train=$4
    model_dest_dir=$dest_dir/$pair/$train
    model_src_dir=$pair_dir/simple/$v/s.train_model.$pair/output
    spm_src_dir=$pair_dir/simple/$v/s.generate_vocab.$(basename $pair_dir)/output
    echo "Copying files for $pair to $model_dest_dir"
    mkdir -p $model_dest_dir
    cp $model_src_dir/model.npz.best-chrf.npz $model_dest_dir
    cp $spm_src_dir/model.$(basename $pair_dir).spm $model_dest_dir

}

for pair_dir in $src_dir/* ; do
    pair=`basename $pair_dir`
    rev_pair=(${pair//-/ })
    rev_pair="${rev_pair[1]}-${rev_pair[0]}"
    
    copy_model $pair_dir $pair v0 hplt
    copy_model $pair_dir $pair v1 opus
    copy_model $pair_dir $pair v2 hplt_opus
    copy_model $pair_dir $rev_pair v0 hplt
    copy_model $pair_dir $rev_pair v1 opus
    copy_model $pair_dir $rev_pair v2 hplt_opus

done

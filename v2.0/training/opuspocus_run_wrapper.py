#!/usr/bin/env python3

#
# Wrapper for executing the OpusPocus pipelines
#

import argparse
import logging
import sys
import time

from pathlib import Path
from omegaconf import OmegaConf

import opuspocus.pipeline_steps as pipeline_steps
import opuspocus.runners as runners
from opuspocus.pipelines import OpusPocusPipeline, PipelineState, load_pipeline
from opuspocus.runners import build_runner


LOG = logging.getLogger(__name__)
PREPROCESS_CONFIG_TEMPLATE = Path(__file__).parent.resolve() / Path("config/opuspocus.preprocess.yml")
TRAIN_CONFIG_TEMPLATE = Path(__file__).parent.resolve() / Path("config/opuspocus.train.yml")


def check_parameters(args):
    if args.preprocess_only and args.train_only:
        LOG.warning("Both --preprocess-only and --train-only were selected. Running the full pipeline.")
        setattr(args, "preprocess_only", False)
        setattr(args, "train_only", False)


def load_preprocess_config(pair, data_version):
    config = OmegaConf.load(PREPROCESS_CONFIG_TEMPLATE)

    setattr(config["global"], "data_ver", data_version)
    setattr(config["global"], "src_lang", pair[0])
    setattr(config["global"], "tgt_lang", pair[1])
    return config


def load_train_config(pair, data_version, marian_dir):
    config = OmegaConf.load(TRAIN_CONFIG_TEMPLATE)

    setattr(config["global"], "data_ver", data_version)
    setattr(config["global"], "src_lang", pair[0])
    setattr(config["global"], "tgt_lang", pair[1])
    setattr(config["global"], "marian_dir", marian_dir)
    return config


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--language", type=str, required=True, help="Specify the pipeline language.")
    parser.add_argument(
        "--data-version", type=str, required=True, choices=["v0", "v1", "v2"], help="Verion of the training data."
    )
    parser.add_argument("--marian-dir", type=str, default="marian", help="Location of MarianNMT.")
    parser.add_argument("--runner", type=str, default="bash", help="Runner used to execute the pipeline.")
    parser.add_argument("--runner-args", type=str, default=None, nargs='+', help="Arguments for the runner.")
    parser.add_argument(
        "--preprocess-only", action="store_true", default=False, help="Run only the data preprocessing."
    )
    parser.add_argument(
        "--train-only", action="store_true", default=False, help="Run only the model training."
    )
    return parser.parse_args()


def main(args):
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(name)s:  %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG
    )

    # Check wrapper parameters
    check_parameters(args)
    pair = sorted([args.language, "en"])

    # Check training data + Run/Skip preprocess
    preprocess_config = load_preprocess_config(pair, args.data_version)
    preprocess_pipeline_dir = Path(preprocess_config["pipeline"]["pipeline_dir"])

    runner_kwargs = argparse.Namespace(**{
        arg.split("=")[0]: "=".join(arg.split("=")[1:])
        for arg in args.runner_args
    })

    if args.train_only:
        preprocess_pipeline = OpusPocusPipeline.load_pipeline(preprocess_pipeline_dir)
    else:
        preprocess_pipeline = OpusPocusPipeline(
            pipeline_dir=preprocess_pipeline_dir,
            pipeline_config=preprocess_config
        )
        preprocess_pipeline.init()

        preprocess_runner = build_runner(args.runner, preprocess_pipeline_dir, runner_kwargs)
        preprocess_runner.run_pipeline(preprocess_pipeline)
        while preprocess_pipeline.state == PipelineState.INITED:
            LOG.debug("Waiting for pipeline submission...")
            time.sleep(300)

    if args.preprocess_only:
        sys.exit()

    # Wait until the preprocessing is finished
    while preprocess_pipeline.state in [PipelineState.RUNNING, PipelineState.SUBMITTED]:
        LOG.debug("Waiting for pipeline to finish...")
        preprocess_pipeline.print_status(preprocess_pipeline.steps)
        time.sleep(300)

    # Run/Skip train
    train_config = load_train_config(pair, args.data_version, args.marian_dir)
    train_pipeline_dir = Path(train_config["pipeline"]["pipeline_dir"])

    pipeline_steps.STEP_INSTANCE_REGISTRY = {}  # reset the registries to be able to create a new pipeline
    train_pipeline = OpusPocusPipeline(
        pipeline_dir=train_pipeline_dir,
        pipeline_config=train_config
    )
    train_pipeline.init()

    train_runner = build_runner(args.runner, train_pipeline_dir, runner_kwargs)
    train_runner.run_pipeline(train_pipeline)


if __name__ == "__main__":
  main(parse_args())

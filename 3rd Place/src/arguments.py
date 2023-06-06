"""
from https://github.com/PatrickHua/SimSiam
"""
import argparse
import os
import random
import re
import shutil
from datetime import datetime

import numpy as np
import torch
import yaml


class Namespace(object):
    def __init__(self, somedict):
        for key, value in somedict.items():
            assert isinstance(key, str) and re.match("[A-Za-z_-]", key)
            if isinstance(value, dict):
                self.__dict__[key] = Namespace(value)
            else:
                self.__dict__[key] = value

    def __getattr__(self, attribute):
        raise AttributeError(
            f"Can not find {attribute} in namespace. Please write {attribute} in your config file(xxx.yaml)!"
        )


def set_deterministic(seed):
    # seed by default is None
    if seed is not None:
        print(f"Deterministic with seed = {seed}")
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config-file", required=True, type=str, help="xxx.yaml")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--debug_subset_size", type=int, default=8)
    parser.add_argument(
        "--download", action="store_true", help="if can't find dataset, download from web"
    )
    parser.add_argument("--log_dir", type=str, default=os.getenv("LOG"))
    parser.add_argument("--ckpt_dir", type=str, default=os.getenv("CHECKPOINT"))
    parser.add_argument(
        "--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu"
    )
    parser.add_argument("--hide_progress", action="store_true")
    parser.add_argument("--flip", action="store_true")
    parser.add_argument("--rot", action="store_true")
    parser.add_argument("--scale", action="store_true")
    args = parser.parse_args()

    with open(args.config_file, "r") as f:
        for key, value in Namespace(yaml.load(f, Loader=yaml.FullLoader)).__dict__.items():
            vars(args)[key] = value

    if args.debug:
        if args.train:
            args.train.batch_size = 2
            args.train.num_epochs = 1
            args.train.stop_at_epoch = 1
        args.dataset.num_workers = 0

    args.log_dir = os.path.join(
        args.log_dir, "in-progress_" + datetime.now().strftime("%m%d%H%M%S_") + args.name
    )

    os.makedirs(args.log_dir, exist_ok=False)
    print(f"creating file {args.log_dir}")
    os.makedirs(args.ckpt_dir, exist_ok=True)

    shutil.copy2(args.config_file, args.log_dir)
    set_deterministic(args.seed)
    vars(args)["dataloader_kwargs"] = {
        "drop_last": True,
        "pin_memory": True,
        "num_workers": args.dataset.num_workers,
    }
    return args

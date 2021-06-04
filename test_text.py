#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Multi-Label Classification"""

import argparse
from tqdm import tqdm
import torch
import torch.nn
import torch.multiprocessing
import preprocessors
from utils.functions import set_seed
from models import *
from datareaders import *
from utils.metrics import *
from utils.config import init_env
import random
from Knowledge import OlympicKnowledge


def main(text, config_path, in_infix, out_infix, gpuid):
    random_seed = 1
    set_seed(random_seed)
    preprocessor = getattr(preprocessors, 'AAPD')(data_path='', random_seed=random_seed)
    texts_idx, labels_origin = preprocessor.load(text)

    config, enable_cuda, device, _ = init_env(config_path, in_infix, out_infix,
                                                   writer_suffix='cls_log_path', gpuid=gpuid)

    texts_idx = torch.tensor(texts_idx[0])
    labels_origin = torch.tensor(labels_origin[0])

    model = E2EMultiLabelCls(config).to(device)
    model.load_parameters(enable_cuda)      # replace=('tar_doc_encoder', 'encoder')

    with torch.no_grad():
        model.eval()
        _, predict = eval_on_model(model=model,
                                         batch_data=[(texts_idx, torch.ones_like(texts_idx), labels_origin)], #
                                         device=device)

    labels = predict[0].gt(0.5).long().tolist()[-1]
    labels = [preprocessor.index_label(idx) for idx, label in enumerate(labels) if label]
    rule_labels = OlympicKnowledge().get_tags(text)
    print(rule_labels)
    diff = list(set(labels).difference(set(rule_labels)))
    if 0 <= random.random() < 0.9:
        if len(rule_labels) > 3:
            rule_labels = rule_labels[:3]
        return rule_labels
    else:
        rule_labels.extend(diff)
        if len(rule_labels) > 3:
            random.shuffle(rule_labels)
            rule_labels = rule_labels[:3]
        return rule_labels

def eval_on_model(model, batch_data, device):
    batch_cnt = len(batch_data)
    all_predict = []
    all_truth = []

    for i, batch in tqdm(enumerate(batch_data), total=batch_cnt, desc='Testing...'):
        # batch data
        batch = [x.to(device) if x is not None else x for x in batch]
        truth = batch[-1]
        all_truth.append(truth)
        batch_input = batch[:-1]
        # forward
        predict = model.forward(*batch_input)
        all_predict.append(predict)

    return None, all_predict


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-text', type=str, default='', help='raw text')
    parser.add_argument('-config', type=str, default='config.yaml', help='config path')
    parser.add_argument('-in', dest='in_infix', type=str, default='default', help='input data_path infix')
    parser.add_argument('-out', type=str, default='default', help='output data_path infix')
    parser.add_argument('-gpuid', type=int, default=None, help='gpuid')
    args = parser.parse_args()

    res = main(args.text, args.config, args.in_infix, args.out, gpuid=args.gpuid)
    print(res)

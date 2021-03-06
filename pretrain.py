#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Han"
__email__ = "liuhan132@foxmail.com"

import argparse
import torch
import torch.nn
import logging
from tqdm import tqdm
from models import LWPT
from datareaders import PTReader
from utils.optims import Optim
from utils.config import init_logging, init_env
from utils.metrics import evaluate_acc

logger = logging.getLogger(__name__)


def main(config_path, in_infix, out_infix, is_train, is_test, gpuid):
    logger.info('-------------LW-PT Pre-Training---------------')
    logger.info('initial environment...')
    config, enable_cuda, device, writer = init_env(config_path, in_infix, out_infix,
                                                   writer_suffix='pt_log_path', gpuid=gpuid)
    logger.info('reading dataset...')
    dataset = PTReader(config)

    logger.info('constructing model...')
    model = LWPT(config).to(device)
    model.load_parameters(enable_cuda)

    # loss function
    criterion = torch.nn.NLLLoss()
    optimizer = Optim(config['train']['optimizer'],
                      lr=config['train']['learning_rate'],
                      max_grad_norm=config['train']['clip_grad_norm'],
                      lr_decay=config['train']['learning_rate_decay'],
                      start_decay_at=config['train']['start_decay_at'])
    optimizer.set_parameters(model.parameters())

    # dataset loader
    batch_train_data = dataset.get_dataloader_train()
    batch_valid_data = dataset.get_dataloader_valid()

    if is_train:
        logger.info('start training...')

        save_steps = config['train']['save_steps']
        eval_steps = config['train']['eval_steps']
        decay_steps = config['train']['decay_steps']

        # train
        model.train()  # set training = True, make sure right dropout
        train_on_model(model=model,
                       criterion=criterion,
                       optimizer=optimizer,
                       dataloader=batch_train_data,
                       valid_dataloader=batch_valid_data,
                       device=device,
                       writer=writer,
                       save_steps=save_steps,
                       eval_steps=eval_steps,
                       decay_steps=decay_steps)

    if is_test:
        logger.info('start testing...')

        with torch.no_grad():
            model.eval()
            valid_acc = eval_on_model(model=model,
                                      dataloader=batch_valid_data,
                                      device=device)
        logger.info("valid_acc=%.2f%%" % (valid_acc * 100))

    writer.close()
    logger.info('finished.')


def train_on_model(model, criterion, optimizer, dataloader, valid_dataloader,
                   device, writer, save_steps, eval_steps, decay_steps):
    num_iters = len(dataloader)
    for step_i, batch in tqdm(enumerate(dataloader), total=len(dataloader), desc='Training...'):
        step_i += 1
        model.zero_grad()

        # batch data
        batch = [x.to(device) if x is not None else x for x in batch]
        cls_truth = batch[-1]
        batch_input = batch[:-1]

        # forward
        model.train()
        cls_predict = model.forward(*batch_input)

        loss = criterion(cls_predict, cls_truth)
        loss.backward()

        # evaluate
        batch_acc, batch_eq_num = evaluate_acc(cls_predict, cls_truth)
        optimizer.step()  # update parameters

        # logging
        batch_loss = loss.item()
        writer.add_scalar('Train-Loss', batch_loss, global_step=step_i)
        writer.add_scalar('Train-Acc', batch_acc, global_step=step_i)

        if step_i % save_steps == 0 or step_i == num_iters:
            logger.debug('Steps %d: loss=%.5f, acc=%.2f%%' % (step_i, batch_loss, batch_acc * 100))
            model.save_parameters(step_i)

        # if step_i % eval_steps == 0 or step_i == num_iters:
        #     with torch.no_grad():
        #         model.eval()
        #         valid_acc = eval_on_model(model=model,
        #                                   dataloader=valid_dataloader,
        #                                   device=device)
        #     writer.add_scalar('Train-Valid-Acc', valid_acc, global_step=step_i)
        #     logger.info("Step %d: valid_acc=%.2f%%" % (step_i, valid_acc * 100))

        # learning rate decay on steps
        if step_i % decay_steps == 0:
            optimizer.updateLearningRate(step_i)  # learning rate decay


def eval_on_model(model, dataloader, device):
    eq_num = 0
    all_num = 0

    for batch in tqdm(dataloader, desc='Evaluating...'):
        # batch data
        batch = [x.to(device) if x is not None else x for x in batch]
        cls_truth = batch[-1]
        batch_input = batch[:-1]

        # forward
        cls_predict = model.forward(*batch_input)
        batch_acc, batch_eq_num = evaluate_acc(cls_predict, cls_truth)

        batch_num = cls_truth.shape[0]
        eq_num += batch_eq_num
        all_num += batch_num

    acc = eq_num / all_num
    return acc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-config', type=str, default='config.yaml', help='config path')
    parser.add_argument('-in', dest='in_infix', type=str, default='default', help='input data_path infix')
    parser.add_argument('-out', type=str, default='default', help='output data_path infix')
    parser.add_argument('-train', action='store_true', default=False, help='enable train step')
    parser.add_argument('-test', action='store_true', default=False, help='enable test step')
    parser.add_argument('-gpuid', type=int, default=None, help='gpuid')
    args = parser.parse_args()

    init_logging(out_infix=args.out)
    main(args.config, args.in_infix, args.out, is_train=args.train, is_test=args.test, gpuid=args.gpuid)

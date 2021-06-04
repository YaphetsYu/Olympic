## Requirements

- Ubuntu 16.04
- Python >= 3.6.0
- PyTorch >= 1.3.0

## Reproducibility

- `--data` and `--outputs`

We provide the proprecessed RMSC and AAPD datasets and pretrained checkpoints of LW-LSTM+PT+FT model and HLW-LSTM+PT+FT model to make sure reproducibility. Please download from the [link](https://mega.nz/file/dLgFTAjB#vgfRg3IcaB17I4iKfgU5aYORabogc5mc2-QiYFvFLs8) and decompress to the root directory of this repository.

```
--data
    |--aapd
    	|--label_test
    	|--label_train
    	...
    aapd_word2vec.model
    aapd_word2vec.model.wv.vectors.npy
    aapd.meta.json
    aapd.pkl
    rmsc_word2vec.model
    rmsc_word2vec.model.wv.vectors.npy
    rmsc.meta.json
    rmsc.pkl
--outputs
    |--aapd
```

> Note that the `data/aapd`and `data/rmsc` is the initial dataset. Here we provide a split of RMSC (i.e. RMSC-V2).

- Testing on AAPD
``` bash
python classification.py -config=aapd.yaml -in=aapd -gpuid [GPU_ID] -test

## Preprocessing
If you want to preprocess the dataset by yourself,  just run the following command with name of dataset (e.g. RMSC or AAPD).
``` bash
PYTHONHASHSEED=1 python preprocess.py -data=AAPD
```
> Note that `PYTHONHASHSEED` is used in word2vec.

## Pre-Train

Pre-train the LW-PT model.

``` bash
python pretrain.py -config=aapd.yaml -gpuid=[GPU_ID] -train -test
```

- `CONFIG_NAME`: `aapd.yaml` 
- `OUT_INFIX`: infix of outputs directory contains logs and checkpoints

## MLTC Task

Train the downstream model for MLTC task.

``` bash
python classification.py -config=[CONFIG_NAME] -in=[IN_INFIX] -out=[OUT_INFIX] -gpuid [GPU_ID] -train -test
python classification.py -config=aapd.yaml -in=default -out=tuned -gpuid=0 -train -test
```

- `IN_INFIX`: infix of inputs directory contains pre-trained checkpoints

## Test Text

``` bash
python test_text.py -text=[TEXT] -config=aapd.yaml -in=default -out=tuned -gpuid=2
```



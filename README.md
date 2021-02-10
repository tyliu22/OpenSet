# OpenSet

## Downloading  Out-of-Distribtion Datasets

### Image datasets
One can download five out-of-distributin datasets from (credit from [facebook research](https://github.com/facebookresearch/odin)):

* **[Tiny-ImageNet (crop)](https://www.dropbox.com/s/avgm2u562itwpkl/Imagenet.tar.gz)**
* **[Tiny-ImageNet (resize)](https://www.dropbox.com/s/kp3my3412u5k9rl/Imagenet_resize.tar.gz)**
* **[LSUN (crop)](https://www.dropbox.com/s/fhtsw1m3qxlwj6h/LSUN.tar.gz)**
* **[LSUN (resize)](https://www.dropbox.com/s/moqh2wh8696c3yl/LSUN_resize.tar.gz)**
* **[iSUN](https://www.dropbox.com/s/ssz7qxfqae0cca5/iSUN.tar.gz)**

### Text datasets


### 

when running this algorithms, please put those datasets into corresponding folders in advance, e.g. .\Dataset\Imagenet_crop.

### Downloading NN Models
One can download training models for CIFAR10 from:

* **[DLA](https://github.com/kuangliu/pytorch-cifar)**

which can achieve 95% accuracy on CIFAR10 dataset. For convenience, we have provided those models on **.\models\dla.py**, and the trainied model parameters are saved in **.\checkpoint\ckpt.pth**.


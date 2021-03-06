'''Train CIFAR10 with PyTorch.'''
import torch
import torch.backends.cudnn as cudnn
import torchvision
import torchvision.transforms as transforms
import torch.nn.functional as F
import matplotlib.pyplot as plt

import os
import argparse
import numpy as np

from models.dla_part import DLA6
from Utils.AUROC_Score_single import AUROC_score
from Utils.MyDataLoader import subDataset
import torch.utils.data.dataloader as DataLoader

r_seed = 0
np.random.seed(r_seed)

# ******************************************************************* #
#                       Para Setting
# ******************************************************************* #

parser = argparse.ArgumentParser(description='PyTorch CIFAR10 Training')
parser.add_argument('--lr', default=0.1, type=float, help='learning rate')
parser.add_argument('--resume', '-r', default=True, action='store_true',
                    help='resume from checkpoint')
args = parser.parse_args()

device = 'cuda' if torch.cuda.is_available() else 'cpu'


# ******************************************************************* #
#                        load Model & CIFAR10
# ******************************************************************* #
best_acc = 0  # best test accuracy
start_epoch = 0  # start from epoch 0 or last checkpoint epoch

print('==> Preparing training data...')
transform_train = transforms.Compose([
    transforms.RandomCrop(32, padding=4),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
])
transform_test = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
])

train_dataset = torchvision.datasets.CIFAR10(
    root='./data', train=True, download=True, transform=transform_train)
test_dataset = torchvision.datasets.CIFAR10(
    root='./data', train=False, download=True, transform=transform_test)

train_dataset_data, train_dataset_label = train_dataset.data, train_dataset.targets
test_dataset_data, test_dataset_label = test_dataset.data, test_dataset.targets
label_class = np.array(list(train_dataset.class_to_idx.values()))
# select 6 classes as training dataset, 4 dataset as testing dataset
np.random.shuffle(label_class)
selected_class, unselected_class= label_class[0:6], label_class[6:10]
print(' CIFAR10 training class:', selected_class)
print('CIFAR10 testing  class:', unselected_class)

selected_train_dataset_label, selected_train_dataset_data = np.empty(shape=[0]), np.empty(shape=[0,32,32,3])
selected_test_dataset_label, selected_test_dataset_data = np.empty(shape=[0]), np.empty(shape=[0,32,32,3])
for i in selected_class:
    selected_train_dataset_data = np.append(selected_train_dataset_data,
                                             train_dataset_data[np.where(train_dataset_label==i)], axis=0)
    selected_train_dataset_label = np.append(selected_train_dataset_label,
                                             np.array(train_dataset_label)[np.where(train_dataset_label==i)])
    selected_test_dataset_data = np.append(selected_test_dataset_data,
                                             test_dataset_data[np.where(test_dataset_label==i)], axis=0)
    selected_test_dataset_label = np.append(selected_test_dataset_label,
                                             np.array(test_dataset_label)[np.where(test_dataset_label==i)])
# selected_train_dataset_label = selected_train_dataset_label.astype(int)
# selected_test_dataset_label = selected_test_dataset_label.astype(int)

# rename label as [0 ,..., 5]
num_class = int(10)
for i in selected_class:
    selected_train_dataset_label[np.where(selected_train_dataset_label==i)] = num_class
    selected_test_dataset_label[np.where(selected_test_dataset_label == i)] = num_class
    num_class = num_class+1
selected_train_dataset_label = (selected_train_dataset_label - 10).astype(int)
selected_test_dataset_label = (selected_test_dataset_label - 10).astype(int)

# numpy dimension [10000, 3, 32, 32]
CIFAR10_train_data, CIFAR10_train_label = selected_train_dataset_data.transpose(0,3,1,2),\
                                      selected_train_dataset_label
CIFAR10_test_data, CIFAR10_test_label = selected_test_dataset_data.transpose(0,3,1,2),\
                                      selected_test_dataset_label

train_dataset = subDataset(CIFAR10_train_data, CIFAR10_train_label)
test_dataset = subDataset(CIFAR10_test_data, CIFAR10_test_label)
train_dataloader = DataLoader.DataLoader(train_dataset, batch_size=128, shuffle=True, num_workers=2)
test_dataloader = DataLoader.DataLoader(test_dataset, batch_size=128, shuffle=True, num_workers=2)




# ******************************************************************* #
#                        Outlier dataset
# ******************************************************************* #
unselected_train_dataset_label = np.empty(shape=[0])
unselected_train_dataset_data = np.empty(shape=[0,32,32,3])
for i in unselected_class:
    unselected_train_dataset_data = np.append(unselected_train_dataset_data,
                                             train_dataset_data[np.where(train_dataset_label==i)], axis=0)
# Data type: array [20000, 3, 32, 32]
Outlier_data = unselected_train_dataset_data.transpose(0,3,1,2)


# ******************************************************************* #
#                        Loading model
# ******************************************************************* #
classes = ('plane', 'car', 'bird', 'cat', 'deer',
           'dog', 'frog', 'horse', 'ship', 'truck')
print('==> Building model..')
net = DLA6()
net = net.to(device)
if device == 'cuda':
    net = torch.nn.DataParallel(net)
    cudnn.benchmark = True
if args.resume:
    # Load checkpoint.
    print('==> Resuming from checkpoint..')
    assert os.path.isdir('checkpoint'), 'Error: no checkpoint directory found!'
    checkpoint = torch.load('./checkpoint/ckpt6.pth')
    net.load_state_dict(checkpoint['net'])
    best_acc = checkpoint['acc']
    start_epoch = checkpoint['epoch']



# ******************************************************************* #
#                        Model embeding
# ******************************************************************* #
# CIFAR10_train_data    Outlier_data

# 2 Float Tensor
CIFAR10_train_data = torch.FloatTensor(CIFAR10_train_data)
Outlier_data = torch.FloatTensor(Outlier_data)

with torch.no_grad():
    result_cifar10_train_last_layer, result_cifar10_train_hidden\
        = net(CIFAR10_train_data.to(device))
    result_cifar10_outlier_last_layer, result_cifar10_outlier_hidden\
        = net(Outlier_data.to(device))

# ******************************************************************* #
#                    Calculating AUROC_score
# ******************************************************************* #
# *********************** AUROC_score ************************* #
num_train_sample = CIFAR10_train_data.shape[0]
num_test_sample = Outlier_data.shape[0]

print('===> AUROC_score start')
# ******************* Outlier Detection ********************** #
# def AUROC_score(train_data_last_layer, train_data_hidden, num_train_sample,
#                 test_data_last_layer, test_data_hidden, num_test_sample,
#                 r_seed=0, n_estimators=1000, verbose=0,
#                 max_samples=10000, contamination=0.01):

for i in range(2,11,1):
    AUROC_score(result_cifar10_train_last_layer, result_cifar10_train_hidden, num_train_sample,
                result_cifar10_outlier_last_layer, result_cifar10_outlier_hidden, num_test_sample,
                r_seed=0, n_estimators=1000, verbose=0, max_samples=1.0, contamination=0.01*i)

print('Algorithm End')


def plot_tsne(features, labels, save_eps=False):
    ''' Plot TSNE figure. Set save_eps=True if you want to save a .eps file.
    '''
    tsne = TSNE(n_components=2, init='pca', random_state=0)
    features_tsne = tsne.fit_transform(features)
    x_min, x_max = np.min(features_tsne, 0), np.max(features_tsne, 0)
    features_norm = (features_tsne - x_min) / (x_max - x_min)
    for i in range(features_norm.shape[0]):
        plt.text(features_norm[i, 0], features_norm[i, 1], str(labels[i]),
                 color=plt.cm.Set1(labels[i] / 10.),
                 fontdict={'weight': 'bold', 'size': 9})
    plt.xticks([])
    plt.yticks([])
    plt.title('T-SNE')
    if save_eps:
        plt.savefig('tsne.eps', dpi=600, format='eps')
    plt.show()


result_mnist_train_hidden = result_mnist_train_hidden.cpu().numpy()
result_mnist_test_hidden = result_mnist_test_hidden.cpu().numpy()
outlier_label = np.ones(5000, dtype=int) + 6
np.random.seed(9527)
np.random.shuffle(result_mnist_train_hidden)
tsne_data = result_mnist_train_hidden[0:5000, :]
np.random.seed(9527)
np.random.shuffle(selected_train_dataset_label)
np.random.shuffle(result_mnist_test_hidden)

tsne_label = selected_train_dataset_label[0:5000]
tsne_data = np.append(tsne_data, result_mnist_test_hidden[0:5000, :], axis=0)
tsne_label = np.append(tsne_label, outlier_label)

# selected_train_dataset_label = np.append(selected_train_dataset_label, outlier_label)
# result_mnist_train_hidden = np.append(result_mnist_train_hidden, result_mnist_test_hidden)

plot_tsne(tsne_data, tsne_label)


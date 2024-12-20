import time
import argparse
import pickle
import os
from BERT_finetuning import NeuralNetwork
import torch




#Dataset path.
FT_data={
    'ubuntu': 'ubuntu_data/ubuntu_dataset_1M.pkl',
    'douban': 'douban_data/douban_dataset_1M.pkl',
    'e_commerce': 'e_commerce_data/e_commerce_dataset_1M.pkl'
}
print(os.getcwd())
## Required parameters
parser = argparse.ArgumentParser()
parser.add_argument("--task",
                    default='ubuntu',
                    type=str,
                    help="The dataset used for training and test.")
parser.add_argument("--is_training",
                    type=str,
                    help="Training model or testing model?")
parser.add_argument("--batch_size",
                    default=64,
                    type=int,
                    help="The batch size.")
parser.add_argument("--learning_rate",
                    default=1e-5,
                    type=float,
                    help="The initial learning rate for Adamw.")
parser.add_argument("--epochs",
                    default=10,
                    type=float,
                    help="Total number of training epochs to perform.")
parser.add_argument("--save_path",
                    default="Fine-Tuning/FT_checkpoint/",
                    type=str,
                    help="The path to save model.")
parser.add_argument("--score_file_path",
                    default="./Fine-Tuning/scorefile.txt",
                    type=str,
                    help="The path to save model.")
parser.add_argument("--do_lower_case", action='store_true', default=True,
                    help="Set this flag if you are using an uncased model.")

args, unknown = parser.parse_known_args()
args.save_path += args.task + '.' + "0.pt"
args.score_file_path = args.score_file_path
# load bert


print(args)
print("Task: ", args.task)


def train_model(train, dev):
    model = NeuralNetwork(args=args)
    print("Training Now")
    model.fit(train, dev)


def test_model(test):
    model = NeuralNetwork(args=args)
    model.load_model(args.save_path)
    model.evaluate(test, is_test=True)


if __name__ == '__main__':
    start = time.time()
    with open(FT_data[args.task], 'rb') as f:   
        train, dev, test = pickle.load(f, encoding='ISO-8859-1')  

    print("Loading Data done")
    end = time.time()
    print("use time: ", (end - start) / 60, " min")
    print("Cuda Available true? ", torch.cuda.is_available())
    start = time.time()

    if args.is_training=='True':
        train_model(train,dev)
        test_model(test)
    else:
        test_model(test)    

    end = time.time()
    print("use time: ", (end - start) / 60, " min")

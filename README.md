# Improving and Evaluating Code Recommender Systems

------------------------------------------------------------------------------------------------------------------------

#### Author: Cristian Buratti
#### Advisor: Prof. Dr. Gabriele Bavota
#### Co-advisors: Dr. Luca Pascarella & Matteo Ciniselli
#### Date: June 2022

------------------------------------------------------------------------------------------------------------------------

This is a Master's Thesis in Software and Data Engineering, supervised by Prof. Dr. Gabriele Bavota, at the 
[Università della Svizzera italiana](https://www.usi.ch/en/). This study extends the previous work done by Ciniselli et 
al. [An Empirical Study on the Usage of Transformer Models for Code Completion](https://github.com/mciniselli/T5_Replication_Package). 

------------------------------------------------------------------------------------------------------------------------

### Replication Package Structure

Our work is divided into three different tasks. For each task we created a folder inside this repository. The first task 
is the replication of the dataset used by Ciniselli et al. The second task is the extraction of code context from the 
mined repository and the corresponding training of different T5 models. The third task is development of a model 
evaluation frameowrk.

------------------------------------------------------------------------------------------------------------------------

### Task 1 - Replication of the Dataset

The Python script used for the first task is available in the `miner` folder. For this entire section we are going to 
assume that the `miner` folder is the root of the project. 

Before you can run this step, you need to install all the dependencies required by the script.

```bash
pip install -r requirements.txt
```

After the installation, you need to download the text files containing the code samples from the original dataset. They
are available [here](TODO). Put the `finetuning` folder you at `miner/data/finetuning` and run the following command:

```bash
python src/main.py
``` 

After the script has finished, you will find a folder named `archives`. This will contain a ZIP file for each repository
that has been successfully mined and checked out to the original version. Moreover, an `out` folder will contain text
files regarding the mining process. One of them will be a list of failed repositories. Another will be called `all.csv`
and will contain all the methods of the dataset.


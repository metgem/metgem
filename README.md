# Build instructions

1. Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

2. Clone the repository:
```
git clone https://github.com/metgem/metgem.git
cd metgem
```

3. Create a new virtual environment
```
conda env create -f environment.yml
```

4. Activate the virtual environment
```
conda activate metgem
```

5. Install build dependencies:
```
conda install invoke
```

6. Build the resource file:
```
invoke packaging.rc
```

7. Launch MetGem
```
python MetGem
```

For later use, you just need to activate the environment before launching MetGem
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/60b6a6283223418fbc3f082b97d86d74)](https://app.codacy.com/manual/n-elie/metgem?utm_source=github.com&utm_medium=referral&utm_content=metgem/metgem&utm_campaign=Badge_Grade_Dashboard)

# Download pre-built packages

You can download the latest stable version from [here](https://github.com/metgem/metgem/releases/latest) or latest development version from [here](https://github.com/metgem/metgem/releases/nightly).

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
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/6bb522a78e5a47688d166a4b8684c3cf)](https://app.codacy.com/gh/metgem/metgem/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

# Download pre-built packages

You can download the latest stable version from [here](https://github.com/metgem/metgem/releases/latest) or latest development version from [here](https://github.com/metgem/metgem/releases/nightly).

# Notes on installation on macOS

Latest versions of MetGem are only compatible with macOS 10.15 Catalina and later.
Currently, MetGem lacks a signature for macOS. As a workaround, user can allow MetGem in the macOS Gatekeeper protection by running the following command in the terminal from the Applications folder.

- Download MetGem and click the .dmg installer - Drag and drop MetGem into the Applications folder.
- Open a Terminal and type the following command to tell macOS to trust the installed version of MetGem:
  ```
  sudo xattr -cr /Applications/MetGem/MetGem.app
  ```
- Approve command with user password.
- Start MetGem.
- If this fails, try the following command (the app will appear in the security preferences and you will be able to choose the "Open anyway" option):
  ```
  sudo xattr -d com.apple.quarantine /Applications/MetGem/MetGem.app
  ```

# Installation from source

1. Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

2. Clone the repository:
```
git clone https://github.com/metgem/metgem.git
cd metgem
```

3. Create a new virtual environment
```
conda env create -f environment.yml
conda env update -f environment.dev.yml
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
invoke rc
```

7. Launch MetGem
```
python MetGem
```

For later use, you just need to activate the environment before launching MetGem

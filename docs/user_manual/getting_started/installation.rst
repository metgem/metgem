.. _website: https://github.com/metgem/metgem/releases/latest
.. _AppImage: https://appimage.org

.. _installation:

Installation
============

Windows
*******

Windows users can download |appname|'s installer from the website_.

.. note::
   |appname| requires Windows 7 or newer.

   
OS X
****

You can download the latest binary from our website_.


.. note::
    The binaries work only with Mac OSX version 10.15 and newer.
    
.. note::
    Currently, MetGem lacks a signature for macOS. As a workaround, user can allow MetGem in the macOS Gatekeeper protection by running the following command in the terminal from the Applications folder.

    - Download MetGem and click the .dmg installer - Drag and drop MetGem into the Applications folder.
    - Open a Terminal and type the following command to tell macOS to trust the installed version of MetGem:

    .. code-block:: bash
    
        sudo xattr -cr /Applications/MetGem/MetGem.app

    - Approve command with user password.
    - Start MetGem.
    - If this fails, try the following command (the app will appear in the security preferences and you will be able to choose the "Open anyway" option):

    .. code-block:: bash
    
        sudo xattr -d com.apple.quarantine /Applications/MetGem/MetGem.app

   
   
Linux
*****

Linux binaries are available from the website_ as an AppImage_. It should be as simple as click and run in any distribution.


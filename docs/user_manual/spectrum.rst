.. |home| image:: /images/icons/home.svg
.. |back| image:: /images/icons/back.svg
.. |forward| image:: /images/icons/forward.svg
.. |move| image:: /images/icons/move.svg
.. |zoom| image:: /images/icons/zoom.svg
.. |save| image:: /images/icons/save.svg
.. |reset| image:: /images/icons/reset.svg

.. _spectrum_view:

Spectrum View
=============

The spectrum view is used to visualize nodes' spectra.

.. image:: /images/spectrum-view.png
  :alt: Spectrum View Window
  
  
The left pane shows the :ref:`loaded spectra <load_spectra>`. You can visualize up to two spectra for comparison.
The top spectrum (in red) is the first one loaded while the second one appears upside-down in the bottom part (in blue).

On the top-right corner of the spectrum, you can see the computed similarity score between the two spectra. Value lies between 0 and 1, the higher it is, the closer the spectra are to each other.

On the lowest part of the window, the legend gives information about which spectra is shown (node index and *m/z* of parent ion).


Matching Peaks List
*******************

When two spectra are loaded, the right-hand pane contains information about which fragments or neutral losses are common to both spectra:

    - The top table list matching fragments,
    - The lower table is for matching neutral losses.
    
Each table has three columns:

    - *Top Spectrum*: *m/z* of fragment or mass of neutral loss in the first spectrum
    - *Bottom Spectrum*: *m/z* of fragment or mass of neutral loss in the second spectrum matching the one of the first spectrum
    - *Partial score*: Contribution of these fragments/losses to the overall matching score. These partial scores add up to the total score.

When a line in this table is selected, the corresponding peaks in the spectra are highlighted. Click anywhere in the table outside any cell to deselect all lines.
    
Toolbar
*******

.. image:: /images/toolbar-spectrum.png
  :alt: Spectrum View Toolbar

Spectrum View come with a navigation toolbar on top of the window, which can be used to navigate through the spectrum. Here is a description of each of the buttons:

 - |home| |back| |forward| *Home*, *Forward* and *Back* buttons are akin to a web browser’s home, forward and back controls. :guilabel:`Forward` and :guilabel:`Back` are used to navigate back and forth between previously defined views. They have no meaning unless you have already navigated somewhere else using the pan and zoom buttons. This is analogous to trying to click :guilabel:`Back` on your web browser before visiting a new page or :guilabel:`Forward` before you have gone back to a page – nothing happens. Home always takes you to the first, default view of your data. Again, all of these buttons should feel very familiar to any user of a web browser.
 - |move| The *Pan/Zoom* button has two modes: pan and zoom. Click the toolbar button to activate panning and zooming, then put your mouse somewhere over an axes. Press the |mouseleft| left mouse button and hold it to pan the figure, dragging it to a new position. When you release it, the data under the point where you pressed will be moved to the point where you released. Press the |mouseright| right mouse button to zoom, dragging it to a new position. The x axis will be zoomed in proportionately to the rightward movement and zoomed out proportionately to the leftward movement. The point under your mouse when you begin the zoom remains stationary, allowing you to zoom in or out around that point as much as you wish.
 - |zoom| Click the *Zoom-to-rectangle* button to activate this mode. Put your mouse somewhere over an axes and press the |mouseleft| left mouse button. Drag the mouse while holding the button to a new location and release. The axes view limits will be zoomed to the rectangle you have defined. There is also an experimental ‘zoom out to rectangle’ in this mode with the |mouseright| right button, which will place your entire axes in the region defined by the zoom out rectangle. You can also zoom in and out using the |mousescroll| mouse wheel.
 - |save| Click the *Save* button to launch a file save dialog. You can save as images with the following extensions: jpg, png, ps, eps, svg, pdf, pgf, tif, raw, and rgba. You can also save spectra as text in the following formats: mgf_ and msp_.
 - |reset| The *Reset* button will simply unload any previously loaded spectrum.
  
  
.. _load_spectra:
  
Load spectra
************
  
To load a spectrum, simply select a node in :ref:`view <network_views>` and use the :menuselection:`View --> Spectrum` menu or the :kbd:`S` shortcut. You can also compare two spectra: select a different node and use the :menuselection:`View --> Compare Spectrum` menu or the :kbd:`C` shortcut. Second spectrum will appear upside-down. Spectra can also be loaded from the :ref:`nodes metadata table <metadata_nodes>`.


Shortcuts
*********

+-----------------------------------------+---------------------------------------------+
| Shortcut                                | Description                                 |
+=========================================+=============================================+
| :kbd:`H`, :kbd:`R`, :kbd:`Home`         | *Home*                                      |
+-----------------------------------------+---------------------------------------------+
| :kbd:`Left`, :kbd:`C`, :kbd:`Backspace` | *Back*                                      |
+-----------------------------------------+---------------------------------------------+
| :kbd:`Right`, :kbd:`V`                  | *Forward*                                   |
+-----------------------------------------+---------------------------------------------+
| :kbd:`P`                                | *Pan/Zoom*                                  |
+-----------------------------------------+---------------------------------------------+
| :kbd:`Shift`                            | Hold to temporarily activate *Pan/Zoom*     |
+-----------------------------------------+---------------------------------------------+
| :kbd:`O`                                | *Zoom To Rect*                              |
+-----------------------------------------+---------------------------------------------+
| :kbd:`Ctrl`                             | Hold to temporarily activate *Zoom To Rect* |
+-----------------------------------------+---------------------------------------------+
| :kbd:`Ctrl` + :kbd:`S`                  | *Save*                                      |
+-----------------------------------------+---------------------------------------------+
| :kbd:`g` when mouse is over an axis     | Toogle major grids                          |
+-----------------------------------------+---------------------------------------------+
| :kbd:`G` when mouse is over an axis     | Toogle minor grids                          |
+-----------------------------------------+---------------------------------------------+

.. _cosine-score: https://en.wikipedia.org/wiki/Cosine_similarity

.. |add-view| image:: /images/icons/list-add.svg
.. |link| image:: /images/icons/chain-link.svg
.. |settings| image:: /images/icons/preferences-system.svg
.. |scale| image:: /images/icons/ruler.svg
.. |lock| image:: /images/icons/lock.svg
.. |zoom-in| image:: /images/icons/zoom-in.svg
.. |zoom-out| image:: /images/icons/zoom-out.svg
.. |zoom-fit| image:: /images/icons/zoom-fit.svg
.. |zoom-target| image:: /images/icons/zoom-target.svg
.. |select-neighbors| image:: /images/icons/select-neighbors.svg
.. |eye| image:: /images/icons/eye.svg
.. |eye-closed| image:: /images/icons/eye-closed.svg
.. |hide-isolated-nodes| image:: /images/icons/hide-isolated-nodes.svg
.. |color| image:: /images/icons/color.svg
.. |node-size| image:: /images/icons/node-size.svg
.. |node-pie| image:: /images/icons/node-pie.svg

.. |scale-slider| image:: /images/view-scale-slider.png
  :alt: Scale Slider
  
.. _network_views:

Network views
=============

.. image:: /images/view.png
  :alt: Example of a View

Data can be visualised using different views. |appname| offers two types of visualisations:

.. _classical_network:

 - **Network**: A classical Molecular Network view like what can be obtained by the  GNPS_ platform. In this view, each node represent an MS/MS spectrum and each edge represent a the distance between two nodes (obtained via a modified `cosine-score`_ calculation). Distance between clusters is arbitrary and has no special meaning.

 .. _2d_projections:
 
 - | **2-D Projections**: A view obtained using a dimension reduction algorithm. This is a 2-D projection of the multidimensional space, so no edge is shown but distance between clusters is informative. To simplify projection, isolated nodes are excluded from the processing and are displayed below the projection. They are arbitrarily distributed and their positions have no special meaning.
   | |appname| can use several algorithm to create a visualisation:
 
    - **t-SNE**: `t-SNE`_ (t-distributed Stochastic Neighboorhodd Embedding) algorithm tends to preserve local distances and distort global distances. This means that, if two clusters are close to each other in the original space, they have statiscally more chance than distant clusters to be close in the `t-SNE`_ projection.
    
    - **U-MAP**: UMAP_ (Uniform Manifold Approximation and Projection) is a quite new algorithm (2018) which is very similar to `t-SNE`_ but claims to preserve both local and most of the global structure in the data.
    
    - **MDS**: MDS_ (MultiDimensional Scaling) is the algorithm on which `t-SNE`_ and UMAP_ are both based. MDS_ doest not try to preserve local distances over global distances.
    
    - **Isomap**: Isomap_ (Isometric mapping) is an extension of the MDS_ algorithm based on the spectral theory which tries to preserve the geodesic distances in the lower dimension.
    
    - **PHATE**: PHATE_ (Potential of Heat-diffusion for Affinity-based Trajectory Embedding) is a tool for visualizing high dimensional data. PHATE_ uses a novel conceptual framework for learning and visualizing the manifold to preserve both local and global distances.


 .. versionchanged:: 1.3
    To make clear that isolated nodes positions are not meaningfull in projections, an horizontal line is drawn between projected nodes and isolated nodes.
    
    
Toolbar
*******
    
.. image:: /images/toolbar-network-view.png
  :alt: Network View Toolbar
  
- |settings| It is possible to change parameters for each visualisation. The visualisation will automatically be re-computed and updated to match the new paramaters.
- |scale| If nodes are too close to each other, you can change the scale of the visualisation using the scale that can be found in the dropdown menu |scale-slider|
- |lock| This option is only available for the :ref:`classical Molecular Network view <classical_network>`. By default, nodes can't be moved to prevent changing their positions by accident. This function let you unlock the view.
    
    
Adding Views
************

You can add view during the :ref:`import data <import_data>` process or later by using the |add-view| :guilabel:`Add View` menu in the :ref:`file_toolbar`.

.. image:: /images/add-view-menu.png
  :alt: Add View Menu
  

Interaction
***********

.. _views_navigation:

Navigation
~~~~~~~~~~

.. image:: /images/toolbar-view.png
  :alt: View Toolbar
  
The :ref:`view_toolbar` can be used to zoom |zoom-in| in or |zoom-out| out the :ref:`active view <navigate_between_views>`. You can also use the |mousescroll| mouse wheel to zoom in or out.

The |zoom-fit| :guilabel:`Zoom to fit` button will reset the zoom to fit all the visible nodes inside the view.

If at least one node is :ref:`selected <views_selection>`, the |zoom-target| :guilabel:`Zoom to the selected region` will adjust the zoom level to fit the selected nodes inside the view. This can be helpfull to easily locate nodes selected from the :ref:`metadata_nodes` nodes metadata table.

.. note:: Aspect of nodes and edges depends on the zooming level. At lower level of zoom, nodes text, :ref:`pie charts <nodes_toolbar_mapping>` and edges are not rendered.


.. _minimap:
  
Minimap
-------

.. image:: /images/view-minimap.png
  :alt: Minimap

The minimap, located on bottom-right edge of each visualisation, gives you a overview of the global representation. It can be used to navigate trough the whole visualisation in two different ways when the :

    - |mouseleft| Left click anywhere in the minimap (outside of the :b_cyan:`light blue` rectangle), the global view will immediately be centered on the selected point.
    - |mouseleft| Left click anywhere in the :b_cyan:`light blue` rectangle and drag it to another point to move the global view.
    
The minimap can be hidden by hitting the :kbd:`M` key on :ref:`active view <navigate_between_views>`.


.. _views_selection:

Selection
~~~~~~~~~
    
Selection can be done with |mouseleft| left click on a node/edge or by selecting a region with |mouseright| right mouse button. Selected nodes turn yellow while selected edges are highlighted in red.
Multiple selections can also be made by holding down the :kbd:`Ctrl` key while left-clicking the selection.

Another way to select nodes is the |select-neighbors| :guilabel:`Select neighbors` button in the :ref:`network_toolbar`.

Selecting nodes or edges will automatically filter metadata tables to show only metadata from selected nodes/edges (See :ref:`metadata_tables`).

By default, selection is linked between view, i.e. when a node is selected in a view, the corresponding node is automatically selected in all other views. This is usefull to see correspondances between views. This behavior can be deactivated using the |link| :guilabel:`Link selection between views` button from the :ref:`network_toolbar`.


View MS/MS spectrum
~~~~~~~~~~~~~~~~~~~

When a node is :ref:`selected <views_selection>`, the MS/MS spectrum it represents can be loaded in the Spectrum View (See :ref:`spectrum_view`).


.. _views_nodes_visibility:

Nodes visibility
~~~~~~~~~~~~~~~~

:ref:`Selected <views_selection>` nodes and edges can be temporarily hidden using the |eye-closed| :guilabel:`Hide selected nodes and edges` button from the :ref:`network_toolbar`. Bring them back using the |eye| :guilabel:`Show all button and edges` button.

Sometimes you may want to hide isolated nodes because they are not really informative and they use a lot of space in the screen. This is a job for Clyde, our cute little ghost standing on the |hide-isolated-nodes| :guilabel:`Show/hide isolated nodes` button!


.. _views_mappings:

Mappings
~~~~~~~~

:ref:`Nodes metadata <metadata_nodes>` can be used to modify how the nodes will look like (See :ref:`nodes_toolbar_mapping`). It is also possible to bypass these mappings:

    - |color| Set the color of the selected node(s). You can use the current color (visible on the top-left corner of the button) or choose another color using dropdown window.
    - |node-size| Adjust size for the selected nodes(s). Select the desired size using the dropdown menu or type it in the text box. Default node size is 30.
    
If you added :ref:`pie charts <nodes_toolbar_mapping>` to nodes, you might want to temporarily disable them. The |node-pie| :guilabel:`Hide Pie Charts` button will be of great help in this task.


.. _navigate_between_views:

Navigate between views
**********************

You have two options to navigate between network views: either |mouseleft| click inside a view or use the :kbd:`Ctrl` + :kbd:`Tab` shortcut. Current view will have a :b_cyan:`light blue` outline.


Keyboard shortcuts
******************

All these shortcuts apply to the :ref:`active view <navigate_between_views>`.

+---------------------------------------+-------------------------------------------------------------------------------------------------+
| Shortcut                              | Description                                                                                     |
+=======================================+=================================================================================================+
| :kbd:`M`                              | Show/hide the :ref:`minimap`                                                                    |
+---------------------------------------+-------------------------------------------------------------------------------------------------+
| :kbd:`S`                              | Show the spectrum associated to the selected node in the :ref:`spectrum_view`                   |
+---------------------------------------+-------------------------------------------------------------------------------------------------+
| :kbd:`C`                              | Compare the spectrum associated to the selected node to another one in the :ref:`spectrum_view` |
+---------------------------------------+-------------------------------------------------------------------------------------------------+
| :kbd:`Ctrl` + :kbd:`C`                | Copy as image the visible part of the active view to the clipboard                              |
+---------------------------------------+-------------------------------------------------------------------------------------------------+
| :kbd:`Ctrl` + :kbd:`Shift` + :kbd:`C` | Copy as image the full active view to the clipboard                                             |
+---------------------------------------+-------------------------------------------------------------------------------------------------+


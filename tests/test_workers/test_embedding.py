from metgem_app.workers.core import TSNEWorker, MDSWorker, IsomapWorker, UMAPWorker, PHATEWorker
import pytest


@pytest.mark.parametrize("worker_class", [TSNEWorker, MDSWorker, IsomapWorker, UMAPWorker, PHATEWorker])
def test_import_modules(worker_class):
    worker_class.import_modules()

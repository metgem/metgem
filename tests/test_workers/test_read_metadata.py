from metgem_app.workers import ReadMetadataWorker, ReadMetadataOptions
import pandas as pd


def test_read_metadata_worker(examples):
    options = ReadMetadataOptions()
    options.sep = ';'
    worker = ReadMetadataWorker(str(examples / 'Stillingia SFE.csv'), options)
    df = worker.run()

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (451, 11)

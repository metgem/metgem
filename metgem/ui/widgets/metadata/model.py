try:
    import os
    import pandas as pd
    with open(os.path.join(os.path.dirname(__file__), 'neutral_losses.csv'), encoding='utf-8') as f:
        pass
except (ImportError, FileNotFoundError, IOError, pd.errors.ParserError, pd.errors.EmptyDataError):
    pass






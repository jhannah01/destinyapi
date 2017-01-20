class DAPIError(Exception):
    def __init__(self, error_msg, results={}, base_ex=None, *args, **kwargs):
        super(DAPIError, self).__init__(error_msg)
        self.error_msg = error_msg
        self.results = results
        self.base_ex = base_ex

__all__ = ['DAPIError']

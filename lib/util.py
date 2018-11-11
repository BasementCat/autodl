def format_bytes(sz):
    divisors = [
        (1024 ** 4, 'TB'),
        (1024 ** 3, 'GB'),
        (1024 ** 2, 'MB'),
        (1024, 'KB'),
        (0, 'B'),
    ]
    for div, suffix in divisors:
        if sz >= div:
            if div == 0:
                return '0B'
            return '{:0.2f}{:s}'.format(sz / float(div), suffix)

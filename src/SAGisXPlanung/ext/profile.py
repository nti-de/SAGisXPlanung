import cProfile
import io
import pstats
from functools import wraps


def profile_it(sort_by='cumtime', lines=30, dump_file=None):
    """
    Decorator to profile a function using cProfile.

    Args:
        sort_by (str): Sorting key for stats (e.g., 'cumtime', 'tottime', 'calls').
        lines (int): Number of lines to print.
        dump_file (str): Optional path to dump full profile data for visualization.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            pr = cProfile.Profile()
            pr.enable()
            try:
                return func(*args, **kwargs)
            finally:
                pr.disable()
                s = io.StringIO()
                ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
                ps.print_stats(lines)

                print(f"\n[PROFILE] Function: {func.__name__}")
                print(s.getvalue())

                if dump_file:
                    ps.dump_stats(dump_file)
                    print(f"[PROFILE] Full stats saved to {dump_file}")
        return wrapper
    return decorator
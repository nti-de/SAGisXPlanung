import nest_asyncio
import pytest


def run_all():
    nest_asyncio.apply()
    exit_code = pytest.main(["--cov=SAGisXPlanung", "--cache-clear", "--cov-report=term-missing", "--asyncio-mode=auto"])
    if int(exit_code) == 0:
        print('Ran OK')
    else:
        pytest.exit('tests failed', returncode=1)


if __name__ == '__main__':
    run_all()

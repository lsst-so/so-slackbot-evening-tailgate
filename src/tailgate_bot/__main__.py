"""Allow ``python -m tailgate_bot`` as an alternative to the console script."""
from .app import main

if __name__ == "__main__":
    main()

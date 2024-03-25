class SingletonMeta(type):
    """
    A General purpose singleton class.

    To be used as a metaclass for a class that should
    only have one instance.

    Example:
    ```
    class MyClass(metaclass=SingletonMeta):
        pass
    ```
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        If the class has not been instantiated, create an instance
        and store it in the _instances dictionary.
        Otherwise, return the instance that has already been created.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

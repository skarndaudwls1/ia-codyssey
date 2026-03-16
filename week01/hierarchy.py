def print_hierarchy(exception, indent=0):
    print(' ' * indent + exception.__name__)
    for subclass in exception.__subclasses__():
        print_hierarchy(subclass, indent + 4)

print_hierarchy(BaseException)
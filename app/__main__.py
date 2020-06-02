from . import serve

def main():
    serve()

try:
    main()
except BaseException as e:
    print(e)
    pass




def _func():
    from tests._configExample2 import conf as conf
    print(conf.conf1Int)
    print(conf.conf1List)
    if conf.conf1Int != -10 or conf.conf1List != [10,20,30]:
        raise RuntimeError()

def main():
    import multiprocessing
    from tests._configExample2 import conf

    conf.conf1Int = -10
    conf.conf1List = [10, 20, 30]


    def run():

        for context in ["fork", "forkserver", "spawn"]:  # Only fork seems to be working
            print(context)
            p = multiprocessing.get_context(context).Process(target=_func)
            p.start()
            p.join()
            assert p.exitcode == 0
    run()

if __name__ == "__main__":
    main()
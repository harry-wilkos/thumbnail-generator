import inspect
import return_thread


def pre_process(args):

    # Extract args 
    if len(args) == 1 and type(args[0]) is list:
        values = args[0]
    else:
        values = list(args)

    # Bundle multiple args for function
    for i in range(len(values)):
        if type(values[i]) is not list:
            values = [values]
            break

    return values


def thread(function, *args):

    args = pre_process(args)

    # Catch incorrect number of args
    for c in range(len(args)):
        if len(args[c]) != len(inspect.getfullargspec(function)[0]):
            return "ERROR: Incorrect number of args passed"
        
    # Start threads and collect them   
    thread_d = {}
    for r, i in enumerate(args):
        thread = return_thread.return_thread(target=function, args=i)
        thread.start()
        thread_d[r] = thread

    return thread_d


def retrieve(*threads_d):

    # Pass on error info from start threads
    if type(threads_d[0]) is str and "ERROR" in threads_d[0]:
        return threads_d[0]
    else:
        collect = []

    # Retrieve Multiple Results
        if len(threads_d) != 1:
            for threads in threads_d:
                results = []
                for i in threads:
                    results.append(threads[i].join())
                collect.append(results)

        else:
            threads = threads_d[0]
            if type(threads) is not list:
                for i in threads:
                    collect.append(threads[i].join())
            else:
                for __thread in threads:
                    results = []
                    for i in __thread:
                        results.append(__thread[i].join())
                    collect.append(results)

    # Extract single result from list
        if len(collect) == 1:
            collect = collect[0]
    return collect


if __name__ == "__main__":
    pass
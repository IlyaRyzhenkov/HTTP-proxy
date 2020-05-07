import argparse
import server


def parse_args():
    arg_parser = argparse.ArgumentParser('HTTP proxy server')
    arg_parser.add_argument('-p', '--port', metavar='port',
                            help='Port to scan (default is 12345)',
                            type=check_port, default=12345)
    arg_parser.add_argument('-f', '--filter', metavar='filter',
                            default='filter.txt', help='Set filter file (default is filter.txt)')
    arg_parser.add_argument('-v', '--verbose', help='Verbose mode', action='store_true')
    arg_parser.add_argument('-a', '--adblock', metavar='adblock', help='Chose adblock rules (regex) file')
    res = arg_parser.parse_args()
    port = res.port
    filter_filename = res.filter
    verbose = res.verbose
    if res.adblock:
        adblock = res.adblock
    else:
        adblock = None
    return port, filter_filename, verbose, adblock


def check_port(port):
    if not (0 <= int(port) <= 65535):
        raise argparse.ArgumentTypeError
    return int(port)


if __name__ == "__main__":
    localhost='127.0.0.1'
    port, filter_filename, verbose, adblock = parse_args()
    host = server.HTTPProxy.get_host()
    serv = server.HTTPProxy(localhost, port)
    serv.set_verbose(verbose)
    serv.set_filter(filter_filename)
    if adblock:
        serv.set_addblock(adblock)
    serv.run()

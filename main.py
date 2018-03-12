#!/bin/env python3
import socket
import argparse
import platform

"""
# TODO
- support gzip
- probably more
"""

REQ = "{method} {path} HTTP/1.1\r\nHost: {host}:{port}\r\nConnection: close\r\n{headers}\r\n{data}\r\n"

METHODS = ['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'CONNECT', 'TRACE']
VERSION = "1.0.1"
HEADERS = {"User-agent":f"pyhttp/{VERSION}", "Accept-Encoding": "deflate", "Accept": "*/*"}

def stripheaders(da, header_only=False):
    header = da.split('\r\n\r\n', 1)[0]
    data = da.split('\r\n\r\n', 1)[1]
    if header_only:
        return header
    return header, data

def hdict2str(dic):
    ret = ""
    for key, value in dic.items():
        ret += key.title() + ": " + value + "\r\n"
    return ret

def str2hdict(st):
    ret = {}
    for line in st.splitlines():
        if line.startswith('HTTP'):
            ret['code'] = [int(s) for s in line.split() if s.isdigit()][0]
            continue
        ret[line.split(': ')[0]] = line.split(': ')[1].split('\r', 1)[0]
    return ret

def parse_url(url):
    if not url.startswith('http://'):
        raise ValueError('URL must start with http://')
    scheme, _, host = url.split('/', 2)
    if '/' in host:
        path = '/' + host.split('/', 1)[1]
    else:
        path = '/'
    host = host.split('/')[0]
    port = host.split(':')[1] if ':' in host else '80'
    host = host.split(':')[0] if ':' in host else host
    return scheme, host, int(port), path

def handle_headers(args):
    global HEADERS
    if args.no_default_headers:
        HEADERS = {}
    if args.headers:
        for i in args.headers:
            HEADERS[i.split(':')[0]] = i.split(':')[1]

def read(so):
    ret = ""
    pdata = so.recv(1024)
    while pdata:
        try:
            ret += pdata.decode()
        except UnicodeDecodeError:
            pass
        pdata = so.recv(1024)
    return ret

def request(host, port, path, headers, method, data):
    if data:
        headers['Content-Type'] = 'text/plain'
        headers['Content-Length'] = str(len(data))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(REQ.format(method=method, path=path, host=host, headers=hdict2str(HEADERS), data=data, port=port).encode())
    rdata = read(s)
    s.close()
    return stripheaders(rdata)

def main(args):
    while True:
        scheme, host, port, path = parse_url(args.url)
        if args.method is None:
            args.method = "GET"
        if not args.method.upper() in METHODS:
            print("WARN: unrecognised method: {}, continuing anyways...".format(args.method.upper()))
        handle_headers(args)
        reqh, reqd = request(host, port, path, HEADERS, args.method.upper(), args.data)
        print(reqd)
        headers = str2hdict(reqh)
        if args.verbose:
            print(headers)
        if headers['code'] >= 400 or headers['code'] < 300 or not args.redirect:
            break
        args.url = headers['Location']

if __name__== "__main__":
    parser = argparse.ArgumentParser("pyhttp", description="a non-interactive network retriever, written in Python")
    parser.version = "pyhttp {} ({})".format(VERSION, platform.platform())
    parser.add_argument('url', help="URL to work with")
    parser.add_argument('-V', '--verbose', help="Make the operation more talkative", action="store_true")
    parser.add_argument('-v', '--version', help="Show the version number and quit", action="version")
    parser.add_argument('-M', '--method', help="Method used for HTTP request")
    parser.add_argument('-D', '--data', help="Data to send in request", default="")
    parser.add_argument('-H', '--headers', help="Send custom headers", default=[], nargs='*')
    parser.add_argument('-R', '--redirect', help="Follow redirects", action="store_true")
    parser.add_argument('--no-default-headers', help="Only send custom headers", action="store_true")
    args = parser.parse_args()
    main(args)
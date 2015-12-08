#!/usr/bin/python

from sys import stderr
from itertools import product
from re import findall
from time import sleep
from argparse import ArgumentParser
from urllib.request import urlopen
from multiprocessing import Pool

import gettext

gettext.install('bcfree', './locale')

T_UNKNOWN = '_'
T_UNKNOWNA = '*'
T_ERROR = 'E'
T_MONEY = '-'
T_TRACK = '.'
T_GOOD = '!'

TEMPLATE = "http://bandcamp.com/tag/{0}?sort_field=date"
TEMPLATEP = "http://bandcamp.com/tag/{0}?sort_field=date&page={1}"
TAGSPAGE = "http://bandcamp.com/tags"


def get_page(url, times=7):
    try:
        with urlopen(url, None, 4) as f:
            data = f.read()
    except Exception as e:
        if times:
            return get_page(url, times-1)
        else:
            return
    return data.decode('utf-8')


def get_album_links_from_page(url):
    print(".", end="", flush=True, file=stderr)
    page = get_page(url)
    if not page:
        sleep(1)
        return get_album_links_from_page(url)
    return findall(r'http\S+/album/[^"]+', page)


def get_links(tags, num=0, processes=10):
    pgs = [TEMPLATE.format(t) for t in tags]
    if num:
        pgs += [TEMPLATEP.format(x,y) for x,y in product(tags, range(1,num+1))]
    print(_("processing list pages: {}").format("a"*len(pgs))+"\033[1F", file=stderr)
    print(_("processing list pages: "), end='', file=stderr)
    with Pool(processes=min(len(pgs), processes)) as pool:
        links = [x for lst in pool.map(get_album_links_from_page, pgs)
                 for x in lst]
    return links


def get_page_type(page):
    if not page:
        return T_ERROR
    elif 'base-text-color">&nbsp;' in page:
        return T_MONEY
    elif ("name your price" in page) or ("Free Download" in page):
        return T_GOOD
    else:
        return T_UNKNOWN


def get_page_status(link):
    page = get_page(link)
    t = get_page_type(page)
    print(t, end='', flush=True, file=stderr)
    return link, t


def main():
    parser = ArgumentParser(description=_('Get links for FREE bandcamp ALBUMS.'))
    parser.add_argument('tags', metavar='TAG', type=str, nargs='+',
                        help=_('tags to process (e.g. "black-metal" or "punk")'))
    parser.add_argument('-t', '--taglist', action="store_true",
                        help=_('show list of valid tags and exit'))
    parser.add_argument('-n', '--num', type=int, default=0,
                        help=_('number of pages to check, 0=check only initial'))
    parser.add_argument('-p', '--processes', type=int, default=10,
                        help=_('number of parallel processes (connections)'))
    options = parser.parse_args()
    if options.taglist:
        print(" ".join(sorted(findall('"/tag/([^"]+)', get_page(TAGSPAGE)))))
        return 0
    todo = set(get_links(options.tags, options.num, options.processes))
    good = []
    sleeptime = 1
    print(file=stderr)  # newline
    while todo:
        linknum = len(todo)
        print(_("got {} links").format(linknum), file=stderr)
        print("{}\033[1F".format('.'*linknum), file=stderr)
        with Pool(processes=options.processes) as pool:
            statuses = pool.map(get_page_status, todo)
        good += [link for link, status in statuses if status == T_GOOD]
        todo = [link for link, status in statuses if status == T_ERROR]
        if todo:
            print("\n"+_("{} pages got error. Waiting {} seconds.").format(len(todo), sleeptime), file=stderr)
            sleep(sleeptime)
            sleeptime += 1
    print(file=stderr)  # newline
    print("\n".join(sorted(good)))


if __name__ == "__main__":
    main()

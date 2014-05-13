#!/usr/bin/python
from math import ceil
from argparse import ArgumentParser
from urllib.request import urlopen

from multiprocessing import Pool

T_UNKNOWN = '_'
T_ERROR = 'E'
T_MONEY = '-'
T_TRACK = '.'
T_GOOD = '!'

TEMPLATE = "http://bandcamp.com/tag/{0}?sort_field=date"
TEMPLATEP = "http://bandcamp.com/tag/{0}?sort_field=date&page={1}"
TAGSPAGE = "http://bandcamp.com/tags"


def get_page(url, times=7):
    try:
        usock = urlopen(url, None, 4)
        data = usock.read()
        usock.close()
    except Exception as e:
        if times:
            return get_page(url, times-1)
        else:
            return
    return data.decode('utf-8')


def get_links_from_page(url):
    print(".", end="", flush=True)
    return [x.split('title')[0].split("href=")[1].strip('" ')
            for x in get_page(url).split('<li class="item">')[1:]]


def get_links(tags, num=0):
    pgs = []
    for tag in tags:
        pgs += [TEMPLATE.format(tag)]
        if num:
            pgs += [TEMPLATEP.format(tag,i) for i in range(1,num+1)]
    with Pool(processes=min(len(pgs), 10)) as pool:
        links = [x for lst in pool.map(get_links_from_page, pgs) for x in lst]
    return links


def get_page_type(page):
    if not page:
        return T_ERROR
    if 'base-text-color">&nbsp;' in page:
        return T_MONEY
    if ("name your price" in page) or ("Free Download" in page):
        try:
            t = page.split('<span class="buyItemPackageTitle primaryText">')[1].split('</span>')[0]
        except:
            return T_UNKNOWN
        if 'track' in t.lower():
            return T_TRACK
        elif 'album' in t.lower():
            return T_GOOD
    return T_UNKNOWN


def get_page_free(link):
    page = get_page(link)
    t = get_page_type(page)
    print(t, end='', flush=True)
    if t == T_GOOD:
       return link


def get_free_p(links, processes):
    with Pool(processes=processes) as pool:
        good = pool.map(get_page_free, links)
    return filter(lambda x: x!=None, good)


def main():
    parser = ArgumentParser(description='Get links for FREE bandcamp ALBUMS.',
                            epilog='to get list of all tags: %(prog)s taglist')
    parser.add_argument('tags', metavar='TAG', type=str, nargs='+',
                        help='Tags to process (e.g. "black-metal" or "punk")')
    parser.add_argument('--num', '-n', type=int, default=0,
                        help='Number of pages to check, 0=check only initial')
    parser.add_argument('--processes', '-p', type=int, default=10,
                        help='Number of parallel processes (connections)')
    options = parser.parse_args()
    if 'taglist' in options.tags:
        print(" ".join(sorted(x.split('"')[0] for x
                              in get_page(TAGSPAGE).split("/tag/"))[2:]))
        return
    links = []
    links = get_links(options.tags, options.num)
    links = set(links)
    print("\ngot {0} links \n".format(len(links))+'_'*len(links))
    p = get_free_p(links, options.processes)
    print("\n"+"\n".join(p))


if __name__ == "__main__":
    main()

#!/usr/bin/python

from sys import argv, exit, stdout
from argparse import ArgumentParser
from urllib.request import urlopen

T_UNKNOWN = '_'
T_ERROR = 'E'
T_MONEY = '-'
T_TRACK = '.'
T_GOOD = '!'

TEMPLATE = "http://bandcamp.com/tag/{0}?sort_field=date"
TEMPLATEP = "http://bandcamp.com/tag/{0}?sort_field=date&page={1}"
TAGSPAGE = "http://bandcamp.com/tags"


def get_page(url, times=3):
    try:
        usock = urlopen(url, None, 2)
        data = usock.read()
        usock.close()
    except Exception as e:
        if times:
            return get_page(url, times-1)
        else:
            return
    return data.decode('utf-8')


def get_links_from_page(url):
    return [x.split('title')[0].split("href=")[1].strip('" ')
            for x in get_page(url).split('<li class="item">')[1:]]


def get_links(tag, num=0, maxpage=1):
    print('[{}] getting page... '.format(tag), end="", flush=True)
    links = get_links_from_page(TEMPLATE.format(tag))
    if not num:
        print()
        return links

    p = 1
    while len(links) < num and p <= maxpage:
        print(p, end="", flush=True)
        links = list(set(get_links_from_page(TEMPLATEP.format(tag,p)) + links))
        p += 1
    print()
    return links[:num]


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


def get_free(links):
    good = []
    for link in links:
        page = get_page(link)
        t = get_page_type(page)
        print(t, end='', flush=True)
        if t == T_GOOD:
            good.append(link)
    return good

def get_taglist():
    return sorted(x.split('"')[0] for x in get_page(TAGSPAGE).split("/tag/"))[2:]



def main():
    parser = ArgumentParser(description='Get links for FREE bandcamp ALBUMS.',
                            epilog='to get list of all tags: %(prog)s taglist')
    parser.add_argument('tags', metavar='TAG', type=str, nargs='+',
                        help='Tags to process (e.g. "black-metal" or "punk")')
    parser.add_argument('--num', '-n', type=int, default=0,
                        help='Number of links to check for each tag')
    parser.add_argument('--maxpage', '-m', type=int, default=10,
                        help='Max page number to process')
    options = parser.parse_args()
    if 'taglist' in options.tags:
        print(" ".join(get_taglist()))
        return
    links = []
    for tag in options.tags:
        links += get_links(tag, options.num, options.maxpage)
    links = set(links)
    print("got {0} links \n".format(len(links))+'_'*len(links))
    print("\n"+"\n".join(get_free(links)))

if __name__ == "__main__":
    main()

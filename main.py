import scholarly as sc
from tqdm import tqdm
import requests
import operator
import os

import numpy as np
import multiprocessing as mp
import sys


def levenshtein(seq1, seq2):
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros((size_x, size_y))
    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x - 1] == seq2[y - 1]:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1],
                    matrix[x, y - 1] + 1
                )
            else:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1] + 1,
                    matrix[x, y - 1] + 1
                )
    return matrix[size_x - 1, size_y - 1]


def fscrape(fname):
    try:
        qry = sc.search_author(fname)
        auth = next(qry).fill()

        bibs = []
        for i, pub in enumerate(auth.publications[1:10]):
            pub.fill()
            # print(pub)

            try:
                if requests.get(pub.bib.get('eprint')).status_code == 200:
                    link = pub.bib['eprint']
                else:
                    link = pub.bib['url']
            except:
                link = pub.bib.get('url', 'https://biomedical.gsu.edu/faculty/')

            author_names = []
            for name in pub.bib.get('author', fname).split(' and '):
                if levenshtein(fname, name) < 3:
                    author_names.append(f'<b>{name}</b>')
                else:
                    author_names.append(name)

            journal = pub.bib.get('journal', 'Journal')

            if journal == 'Journal':
                if 'patent' in link:
                    journal = 'US Patents'

            _bibs = [', '.join(author_names),
                     f"<a href={link}>{pub.bib.get('title', 'Link')}</a>",
                     f'<b>{journal[0].upper() + journal[1:]}</b>',
                     pub.bib.get('year', 'N/A'),
                     pub.bib.get('number', 'N/A') + '(' + pub.bib.get('volume', 'N/A') + ')',  # Issue (Volume)
                     pub.bib.get('pages', 'N/A')]

            bibs.append(_bibs)
            print(f'{fname}: {i + 1}/{len(auth.publications)}')

        bibs.sort(key=operator.itemgetter(3), reverse=True)

        with open(f'outputs{os.sep}{fname}.txt', 'w', encoding="utf-8") as wr:
            wr.write('<ol>\n')
            for author, title, journal, year, num, pages in bibs:
                line = f'{author}. {title}. {journal}. {year};{num}:{pages}.'
                wr.write(f'<li>{line}</li>\n')
                wr.flush()
            wr.write('</ol>')
    except Exception as e:
        print(e)


if __name__ == "__main__":
    faculty = [s.strip('\n') for s in open('Faculty.txt', 'r').readlines()]
    print('Total faculties:', len(faculty))

    threads = int(sys.argv[1])
    print(f'{threads} Threads')
    with mp.Pool(processes=threads) as pool:
        pool.starmap(fscrape, [(f,) for f in faculty])

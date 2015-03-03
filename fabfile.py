import datetime
import json

from bs4 import BeautifulSoup
from fabric.api import *
from feedgen.feed import FeedGenerator
import requests

def current_term():
    now = datetime.datetime.now()
    if now.month < 8:
        return now.year - 1
    else:
        return now.year

@task
def scrape_to_json():
    payload = []
    for term in range(2010, current_term() + 1):
        print term

        term_dict = {}
        term_dict['term'] = term
        term_dict['cases'] = []

        r = requests.get("http://www.supremecourt.gov/oral_arguments/argument_audio/%s" % term)
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.select('table.datatables tr')

        for row in rows:
            cells = row.select('td')

            if len(cells[0].select('a')) > 0:
                case_dict = {}
                case_dict['docket'] = cells[0].text.split('.')[0].strip()
                case_dict['name'] = ".".join(cells[0].text.split('.')[1:]).strip()
                case_dict['date'] = cells[1].text.strip()

                detail = "http://www.supremecourt.gov/oral_arguments/%s" % cells[0].select('a')[0]['href'].strip().split('../')[1].strip()

                r = requests.get(detail)
                detail_soup = BeautifulSoup(r.text, "lxml")

                case_dict['mp3'] = detail_soup.select('#ctl00_ctl00_MainEditable_mainContent_pnlHTML5Audio audio source')[0]['src'].strip()
                case_dict['url'] = detail
                term_dict['cases'].append(case_dict)
                print case_dict

        payload.append(term_dict)

    payload = json.dumps(payload)

    with open('output.json', 'w') as writefile:
        writefile.write(payload)

@task
def generate_podcast():
    fg = FeedGenerator()
    fg.id('https://jeremybowers.com/courtcast/')
    fg.title('CourtCast')
    fg.author({'name':'Jeremy Bowers', 'email':'jeremyjbowers@gmail.com'})
    fg.language('en')
    fg.link(href='http://example.com', rel='alternate')
    fg.logo('http://ex.com/logo.jpg')
    fg.subtitle('This is a cool feed!')
    fg.link(href='http://larskiesow.de/test.atom', rel='self')

    with open('output.json', 'r') as readfile:
        terms = list(json.loads(readfile.read()))

    for term in terms:
        for case in term['cases']:
            title = "(%s) %s" % (term['term'], case['name'])
            description = "Argued: %s Docket number: %s" % (case['date'], case['docket'])
            fe = fg.add_entry()
            fe.id(case['mp3'])
            fe.link(href=case['mp3'], rel='self')
            fe.content(description)
            fe.title(title)

    fg.atom_file('atom.xml')
    fg.rss_file('rss.xml')
import datetime
import json

from bs4 import BeautifulSoup
from dateutil.parser import *
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

    with open('cases.json', 'w') as writefile:
        writefile.write(payload)

@task
def generate_podcast():
    with open('cases.json', 'r') as readfile:
        terms = list(json.loads(readfile.read()))

    for term in terms:
        fg = FeedGenerator()
        fg.id('https://jeremybowers.com/courtcast/%s' % term['term'])
        fg.title('CourtCast: %s term' % term['term'])
        fg.author({'name':'Jeremy Bowers', 'email':'jeremyjbowers@gmail.com'})
        fg.language('en')
        fg.link(href='http://www.supremecourt.gov/oral_arguments/', rel='alternate')
        fg.logo('http://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Government_icon.svg/200px-Government_icon.svg.png')
        fg.subtitle('Oral arguments to the Supreme Court in the %s term.' % term['term'])
        fg.link(href='http://www.supremecourt.gov/oral_arguments/%s' % term['term'], rel='self')

        for case in term['cases']:
            published = parse(case['date'], ignoretz=True)
            title = "(%s) %s" % (term['term'], case['name'])
            description = "Argued: %s Docket number: %s" % (case['date'], case['docket'])

            fe = fg.add_entry()
            fe.id(case['mp3'])
            fe.link(href=case['mp3'], rel='self')
            fe.content(description)
            fe.title(title)
            fe.published()

        fg.atom_file('podcasts/%s.xml' % term['term'])
# COURTCAST
CourtCast transforms the Supreme Court's downloadable [oral argument audio](http://www.supremecourt.gov/oral_arguments/argument_audio.aspx) into standard JSON, ATOM and RSS XML.

## Bootstrap
```
mkvirtualenv courtcast # optional
git clone git@github.com:jeremyjbowers/courtcast.git && cd courtcast
pip install -r requirements.txt
fab scrape_to_json
fab generate_podcast
```
"""Static site generator for the Malmesbury C of E Primary School website.
Run: python generator/build.py  ->  dist/
Page text lives in content/*.md; photos in assets/images; documents in assets/docs."""
import os as _os
BASE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import os
import re
import shutil
import markdown
from jinja2 import Environment, FileSystemLoader
CONTENT = _os.path.join(BASE, 'content')
TEMPLATES = _os.path.join(BASE, 'generator/templates')
DIST = _os.path.join(BASE, 'dist')
PROCESSED_IMAGES = _os.path.join(BASE, 'assets/processed')
FETCHED_IMAGES = _os.path.join(BASE, 'assets/images')
FETCHED_DOCS = _os.path.join(BASE, 'assets/docs')
DOC_LIBRARY_PLAN = _os.path.join(BASE, 'generator/doc_library_plan.json')
HOMEPAGE_ICONS = _os.path.join(BASE, 'assets/homepage_icons')

def _doc_library_categories():
    import json as _json
    with open(DOC_LIBRARY_PLAN, encoding='utf-8') as f:
        data = _json.load(f)
    cats = data.get('categories', {})
    return sorted(((c, u) for c, u in cats.items() if u), key=lambda kv: -len(kv[1]))
PREVIEW_MODE = False
env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=False)
base_tpl = env.get_template('base.html')
META_MARKERS = ['## Images on this page', '## Images', '## Contact Us (footer)', '## Footer navigation', '## Global site navigation']
FRONTMATTER_RE = re.compile('^---\\n.*?\\n---\\n', re.DOTALL)

def strip_body(raw, title=''):
    body = FRONTMATTER_RE.sub('', raw, count=1)
    cut_at = len(body)
    for marker in META_MARKERS:
        idx = body.find(f'\n{marker}')
        if idx != -1:
            cut_at = min(cut_at, idx)
        if body.startswith(marker):
            cut_at = min(cut_at, 0)
    body = body[:cut_at].strip()
    lines = body.split('\n')
    if lines and re.match('^#\\s+\\S', lines[0]):
        heading_text = lines[0].lstrip('#').strip()
        if heading_text.lower() == title.lower():
            lines = lines[1:]
            while lines and (not lines[0].strip()):
                lines = lines[1:]
        else:
            lines[0] = '## ' + heading_text
    return '\n'.join(lines).strip()

def md_to_html(body):
    html = markdown.markdown(body, extensions=['tables', 'sane_lists'])
    return re.sub('<table>.*?</table>', lambda m: f'<div class="table-scroll">{m.group(0)}</div>', html, flags=re.S)

def figure_html(root, src, alt, caption=None, css_class=''):
    cap = f'<figcaption>{caption}</figcaption>' if caption else ''
    return f'<figure class="page-figure {css_class}"><img src="{root}{src}" alt="{alt}" loading="lazy">{cap}</figure>'

def inline_figure_html(root, src, alt, caption=None):
    cap = f'<figcaption>{caption}</figcaption>' if caption else ''
    return f'<figure class="inline-figure"><img src="{root}{src}" alt="{alt}" loading="lazy">{cap}</figure>'

def photo_grid_html(root, photos):
    if not photos:
        return ''
    items = ''.join((f'''<figure class="staff-photo"><img src="{root}{p['src']}" alt="{p['alt']}" loading="lazy"><figcaption>{p['alt']}</figcaption></figure>''' for p in photos))
    return f'<div class="staff-photo-grid">{items}</div>'

def governor_cards_html(root, cards):
    out = []
    for i, c in enumerate(cards):
        side = 'gov-card--white' if i % 2 == 0 else 'gov-card--blue'
        lines = ''.join((f"""<p class="gov-name"><strong><u>{c['lines'][0]}</u></strong></p>""" if n == 0 else f'<p><strong>{line}</strong></p>' for n, line in enumerate(c['lines'])))
        photo = c.get('photo', 'gov-placeholder.jpg')
        alt = c['alt'] if 'photo' in c else ''
        out.append(f'<div class="gov-card {side}"><div class="gov-text">{lines}</div><img class="gov-photo" src="{root}{photo}" alt="{alt}" loading="lazy" width="150" height="150"></div>')
    return '<div class="gov-list">' + ''.join(out) + '</div>'

def person_cards_html(root, people):
    items = ''.join((f'''<div class="person-card"><img class="gov-photo" src="{root}{p['photo']}" alt="{p['name']}" loading="lazy" width="150" height="150"><p class="person-name">{p['name']}</p><p class="person-role">{p['role']}</p></div>''' for p in people))
    return f'<div class="person-cards">{items}</div>'

def photo_rows_html(root, rows):
    from PIL import Image as _Img
    out = []
    for row in rows:
        figs = []
        for src, alt in row:
            w, h = _Img.open(os.path.join(FETCHED_IMAGES, src)).size
            figs.append(f'<figure class="ol-photo" style="flex:{w / h:.3f} 1 0"><img src="{root}{src}" alt="{alt}" loading="lazy" width="{w}" height="{h}"></figure>')
        cls = 'ol-row' + (' ol-row--single' if len(row) == 1 and w / h < 1.8 else '')
        out.append(f'<div class="{cls}">' + ''.join(figs) + '</div>')
    return '<div class="ol-photos">' + ''.join(out) + '</div>'

def doc_library_html(categories):
    if not categories:
        return ''
    from urllib.parse import urlparse, unquote as _unquote
    blocks = []
    for cat, urls in categories:
        items = ''.join((f'<li><a href="{u}">{_unquote(os.path.basename(urlparse(u).path))}</a> (hosted on the original school site)</li>' for u in urls))
        blocks.append(f'<div class="page-downloads"><h2>{cat}</h2><ul>{items}</ul></div>')
    return ''.join(blocks)

def render_homepage(root):
    icons = root + 'images/icons/'

    def card(href, icon, title, text):
        return f'<a class="home-card" href="{root}{href}"><img src="{icons}{icon}" alt="" class="home-card-icon" loading="lazy"><h3>{title}</h3><p>{text}</p></a>'
    hero = '<section class="home-hero"><p class="home-hero-vision">&lsquo;Growing together in wisdom and love; discovering life in all its fullness.&rsquo;</p><p>Welcome to the website of Malmesbury C of E Primary School. We are a school of around 400 pupils, in the historic Wiltshire town of Malmesbury. Our vision statement above summarises everything we aim for: a sense of community, deep learning, emotional flourishing, the excitement of discovery and setting children on a pathway to a fulfilling life.</p><p>This site is full of useful information for anyone with a child at the school, thinking of joining us or just interested in the amazing things which happen here.</p></section>'
    actions = '<h2>Quick Actions</h2><div class="home-cards home-cards-3">' + card('information/term-dates/index.html', 'icon-calendar.png', 'Term Dates', 'School term dates, holidays and training (TD) days for the year.') + card('school-tours/index.html', 'icon-newsletter.png', 'School Tours', 'Booking a date for a school tour for Sept 2027 new starters.') + card('breakfast-club/index.html', 'icon-user.png', 'Peas in the Pod', 'Find out more about our on-site before and after school childcare.') + '</div>'
    news_items = [('news/index.html', 'October 2026: A Planetarium came to school!', 'It filled one half of the hall! Years 5 and 6 are studying Space Explorers this term, but all the children got a session inside …'), ('news/index.html', 'August 2026: SIAMS report published', 'Malmesbury CE Primary School&rsquo;s SIAMS report has been published. We are delighted with our new SIAMS report …'), ('news/index.html', 'July 2026: World Cup breakfast on BBC Breakfast', 'Children arrived early to watch a World Cup match before school. BBC Breakfast came to school and broadcast the event live …')]
    news_cards = ''.join((f'<article class="news-card"><h3><a href="{root}{href}">{title}</a></h3><p>{excerpt}</p><a class="read-more" href="{root}{href}">Read more &rarr;</a></article>' for href, title, excerpt in news_items))
    news = f'<h2>News &amp; Events</h2><div class="news-cards">{news_cards}</div><p class="see-all"><a href="{root}news/index.html">See all news &rarr;</a></p>'
    find_us = f'<section class="home-find-us"><div class="home-find-us-text"><h2>Find Us</h2><p>Malmesbury CE Primary School, Tetbury Hill, Malmesbury, Wiltshire, SN16 9JR.</p><p><a href="{root}travel/index.html">Travel and directions &rarr;</a></p></div><img src="{icons}map.gif" alt="Map showing the school&rsquo;s location in Malmesbury" class="home-find-us-map" loading="lazy"></section>'
    return hero + actions + news + find_us

def gallery_html(root, items):
    if not items:
        return ''
    figs = ''.join((f'''<figure class="gallery-figure"><img src="{root}{i['src']}" alt="{i['alt']}" loading="lazy">''' + (f"<figcaption>{i['caption']}</figcaption>" if i.get('caption') else '') + '</figure>' for i in items))
    return f'<div class="photo-gallery">{figs}</div>'

def author_buttons_html(authors):
    if not authors:
        return ''
    items = ''.join((f'''<a href="{a['href']}" target="_blank" rel="noopener">{a['name']}</a>''' for a in authors))
    return f'<div class="author-buttons">{items}</div>'

def big_buttons_html(buttons):
    if not buttons:
        return ''
    row_class = 'big-button-row' + (' big-button-row--single' if len(buttons) == 1 else '') + (' big-button-row--four' if len(buttons) == 4 else '')
    items = ''.join((f'''<a class="big-button big-button--{b.get('color', 'maroon')}" href="{b['href']}"''' + (' target="_blank" rel="noopener"' if b.get('external') else '') + f">{b['label']}</a>" for b in buttons))
    return f'<div class="{row_class}">{items}</div>'

def divider_heading_html(text):
    return f'<div class="divider-heading"><span class="divider-line"></span><span class="divider-text">{text}</span><span class="divider-line"></span></div>'

def image_button_row_html(root, image, buttons, image_first=True):
    img_html = ''
    if image:
        img_html = f'''<div class="row-image"><img src="{root}{image['src']}" alt="{image['alt']}" loading="lazy"></div>'''
    btn_items = ''.join((f'''<a class="big-button big-button--{b.get('color', 'maroon')}" href="{b['href']}"''' + (' target="_blank" rel="noopener"' if b.get('external') else '') + f">{b['label']}</a>" for b in buttons))
    btn_html = f'<div class="row-buttons">{btn_items}</div>'
    parts = [img_html, btn_html] if image_first else [btn_html, img_html]
    return f"""<div class="button-image-row">{''.join(parts)}</div>"""

def button_grid_html(root, columns):
    cols = []
    for col in columns:
        parts = []
        for it in col:
            if 'image' in it:
                name = it['image'].split('/')[-1]
                if not os.path.exists(os.path.join(FETCHED_IMAGES, name)):
                    continue
                img = f'''<img src="{root}{it['image']}" alt="{it['alt']}" loading="lazy">'''
                if it.get('href'):
                    ext = ' target="_blank" rel="noopener"' if it.get('external') else ''
                    img = f'''<a href="{it['href']}"{ext}>{img}</a>'''
                parts.append(f'<div class="grid-image">{img}</div>')
            elif 'text' in it:
                parts.append(f"""<p class="grid-text">{it['text']}</p>""")
            elif 'html' in it:
                parts.append(f"""<div class="grid-html">{it['html']}</div>""")
            elif it.get('needs') and (not os.path.exists(os.path.join(FETCHED_IMAGES, it['needs']))):
                continue
            elif it.get('needs_doc') and (not os.path.exists(os.path.join(FETCHED_DOCS, it['needs_doc']))):
                continue
            else:
                ext = ' target="_blank" rel="noopener"' if it.get('external') else ''
                parts.append(f'''<a class="big-button big-button--{it.get('color', 'blue')}" href="{it['href']}"{ext}>{it['label']}</a>''')
        cols.append(f"""<div class="grid-col">{''.join(parts)}</div>""")
    return f"""<div class="button-grid button-grid--{len(columns)}">{''.join(cols)}</div>"""

def tabs_html(root, tab_id, tabs):
    btns, panels = ([], [])
    for i, t in enumerate(tabs):
        tid, pid = (f'{tab_id}-tab-{i}', f'{tab_id}-panel-{i}')
        sel = 'true' if i == 0 else 'false'
        btns.append(f'''<button type="button" role="tab" id="{tid}" aria-controls="{pid}" aria-selected="{sel}" tabindex="{(0 if i == 0 else -1)}">{t['label']}</button>''')
        inner = ''
        if t.get('image') and os.path.exists(os.path.join(FETCHED_IMAGES, t['image'].split('/')[-1])):
            inner += f'''<img class="tab-image" src="{root}{t['image']}" alt="{t.get('alt', '')}">'''
        inner += t.get('html', '')
        hidden = '' if i == 0 else ' hidden'
        panels.append(f'''<div class="tab-panel" role="tabpanel" id="{pid}" aria-labelledby="{tid}"{hidden}><h2 class="tab-panel-heading">{t['label']}</h2>{inner}</div>''')
    script = "<script>\n(function(){var w=document.getElementById('%s');if(!w)return;w.classList.add('tabs--js');\nvar b=[].slice.call(w.querySelectorAll('[role=tab]')),p=[].slice.call(w.querySelectorAll('[role=tabpanel]'));\nfunction show(i,f){b.forEach(function(x,j){x.setAttribute('aria-selected',j===i);x.tabIndex=j===i?0:-1;p[j].hidden=j!==i;});if(f)b[i].focus();}\nb.forEach(function(x,i){x.addEventListener('click',function(){show(i);});x.addEventListener('keydown',function(e){\nif(e.key==='ArrowRight'){show((i+1)%%b.length,1);e.preventDefault();}if(e.key==='ArrowLeft'){show((i-1+b.length)%%b.length,1);e.preventDefault();}});});\nshow(0);})();\n</script>" % tab_id
    return f'''<div class="tabs" id="{tab_id}"><div class="tab-list" role="tablist">{''.join(btns)}</div>{''.join(panels)}</div>{script}'''

def report_links_html(root, links):
    if not links:
        return ''
    items = ''.join((f'''<a class="home-card" href="{l['href']}" target="_blank" rel="noopener"><img src="{root}images/{l['icon']}" alt="" class="home-card-icon" loading="lazy"><h3>{l['label']}</h3><p>{l.get('text', 'Opens in a new tab.')}</p></a>''' for l in links))
    return f'<div class="home-cards report-links">{items}</div>'

def downloads_html(root, downloads):
    if not downloads:
        return ''
    items = ''.join((f'''<li><a href="{(d['href'] if d.get('external') else root + 'documents/' + d['href'])}">{d['label']}</a>{(' (hosted on the original school site)' if d.get('external') else '')}</li>''' for d in downloads))
    return f'<div class="page-downloads"><h2>Downloads</h2><ul>{items}</ul></div>'
GOVERNOR_CARDS = [{'photo': 'gov-laurence-mussett.jpg',
  'alt': 'Laurence Mussett',
  'lines': ['Laurence Mussett, Chair of Governors, Community Governor and Governor for Attendance.',
            'Serves on the Finance &amp; Premises Committee',
            'Appointed by Members (4 year term) – 23/11/2024 – 22/11/2028']},
 {'photo': 'gov-julie-brown.jpg',
  'alt': 'Julie Brown',
  'lines': ['Julie Brown, Vice Chair of Governors, Community Governor, SEND Governor',
            'Co-Chair of the Staffing &amp; Curriculum Committee and serves on the School Expansion '
            'Committee',
            'Appointed by Members (4 year term) – 23/11/2024 – 22/11/2028']},
 {'photo': 'gov-nigel-roberts.jpg',
  'alt': 'Nigel Roberts',
  'lines': ['Nigel Roberts, Community Governor, Governor for Health and Safety, Governor for Children Looked '
            'After and Governor for PE',
            'Vice Chair of the Finance &amp; Premises Committee and the Audit &amp; Risk Committee, and '
            'serves on the School Expansion Committee',
            'Appointed by Members (4 year term) – 23/11/2024 – 22/11/2028']},
 {'lines': ['Ewen Vizor, Community Governor, Governor for Safeguarding, Online Safety and Governor for Sex '
            'and Relationship Education',
            'Serves on the Staffing &amp; Curriculum Committee',
            'Appointed by Members (4 year term) – 23/11/2024 – 22/11/2028']},
 {'photo': 'gov-rachael-pink.jpg',
  'alt': 'Rachael Pink',
  'lines': ['Rachael Pink, Community Governor, Governor for Allergies',
            'Chair of the Finance &amp; Premises Committee and the Audit &amp; Risk Committee, and serves on '
            'the School Expansion Committee',
            'Appointed by Members (4 year term) – 15/12/2025 – 14/12/2029']},
 {'lines': ['Ben Williams, Foundation Governor, Governor for RE',
            'Appointed by the Diocese (4 year term) – 04/12/2024 – 03/12/2028',
            'Serves on the Finance &amp; Premises Committee and the Audit &amp; Risk Committee']},
 {'lines': ['Tara Lochery, Parent Governor',
            'Serves on the Staffing &amp; Curriculum Committee',
            'Elected by parents of the school (4 year term) – 25/11/2025 – 24/11/2029']},
 {'lines': ['Dalia ElEdel, Parent Governor',
            'Co-Chair of the Staffing and Curriculum Committee',
            'Elected by parents of the school (4 year term) – 10/02/2023 – 09/02/2027']},
 {'lines': ['Joanna Stephens, Parent Governor',
            'Serves on the Finance &amp; Premises Committee',
            'Elected by the parents of the school (4 year term) – 16/10/2025 – 15/10/2029']},
 {'lines': ['Hiteshree Patel, Parent Governor',
            'Serves on the Staffing &amp; Curriculum Committee and the School Expansion Committee',
            'Elected by parents of the school (4 year term) – 17/11/2024 – 16/11/2028']},
 {'lines': ['Chris Russell, Parent Governor',
            'Serves on the Staffing &amp; Curriculum Committee',
            'Elected by the parents of the school (4 year term) – 25/11/2025 – 24/11/2029']},
 {'photo': 'gov-jonathan-watkins.jpg',
  'alt': 'Jonathan Watkins',
  'lines': ['Jonathan Watkins, Staff Governor',
            'Serves on the Finance &amp; Premises Committee and the Staffing &amp; Curriculum Committee',
            'Appointed by the Governing Body (4 year term) – 17/03/2026 – 16/03/2030']},
 {'lines': ['Paula Muir McLeod, Associate Member',
            'Serves on the School Expansion Committee and the Staffing &amp; Curriculum Committee (with '
            'voting rights)',
            'Appointed by the Governing Body (4 year term) – 22/10/2025 – 21/10/2029']},
 {'lines': ['Alison Gravatt, Associate Member',
            'Serves on the Finance &amp; Premises Committee and the Staffing &amp; Curriculum Committee '
            '(with voting rights)',
            'Appointed by the Governing Body (4 year term) – 20/05/2025 – 19/05/2029']},
 {'photo': 'gov-judith-brown.jpg',
  'alt': 'Judith Brown',
  'lines': ['Judith Brown, Associate Member',
            'Serves on the School Expansion Committee (with voting rights)',
            'Appointed by the Governing Body (4 year term) – 17/03/2026 – 16/03/2030']},
 {'photo': 'gov-stephen-heal.jpg',
  'alt': 'Stephen Heal',
  'lines': ['Stephen Heal, Ex Officio Governor',
            'Serves on the Finance &amp; Premises Committee, the Staffing &amp; Curriculum Committee and the '
            'School Expansion Committee',
            'Headteacher (continuous term)']}]
PAGES = [{'src': 'home/index.md', 'out': '', 'section': '', 'title': 'Home'},
 {'src': 'home/headteachers-welcome.md',
  'out': 'headteachers-welcome/',
  'section': 'Home',
  'portraits': {'HEAD_PHOTO': {'src': 'photos/Stephen_Heal.jpg', 'alt': 'Steve Heal, headteacher'}}},
 {'src': 'news/index.md',
  'out': 'news/',
  'section': 'Home',
  'title': 'News',
  'button_rows': {'NEWSLETTER_BUTTONS': [{'label': 'Primary Post 272 – September 2026',
                                          'href': '/documents/Primary-Post-272-September-2026.pdf',
                                          'color': 'navy'},
                                         {'label': 'Primary Post 271 – July 2026',
                                          'href': '/documents/Primary-Post-271-July-2026.pdf',
                                          'color': 'blue'},
                                         {'label': 'Primary Post 270 – June 2026',
                                          'href': '/documents/Primary-Post-270-June-2026.pdf',
                                          'color': 'teal'}]},
  'portraits': {'PLANETARIUM_PHOTO': {'src': 'photos/planetarium.jpg',
                                      'cls': 'news-photo',
                                      'alt': 'An inflatable purple and silver striped planetarium dome set '
                                             'up in the school hall'},
                'DYSON_PHOTO': {'src': 'photos/Dyson-visit-pixelated.jpg',
                                'cls': 'news-photo',
                                'alt': 'Sir James Dyson and Nick Robinson of BBC Radio 4 with pupils looking '
                                       'at a model built from Dyson parts'}}},
 {'src': 'news/adhd-awareness-month.md', 'out': 'news/adhd-awareness-month/', 'section': 'Home > News'},
 {'src': 'news/autism-acceptance-month-2026.md',
  'out': 'news/autism-acceptance-month-2026/',
  'section': 'Home > News'},
 {'src': 'about/our-staff-team.md', 'out': 'about/our-staff-team/', 'section': 'About'},
 {'src': 'about/expansion-project-planning.md',
  'out': 'about/our-vision-and-expansion/',
  'section': 'About',
  'title': 'Our Vision & Expansion',
  'hero_image': 'vision-expansion-aerial.jpg',
  'downloads': [{'href': 'Malmesbury-CE-Primary-School-Vision-2025.pdf',
                 'label': 'School Vision Statement 2025 (PDF)'},
                {'href': 'JDF_Malmesbury-School_Press-release.pdf',
                 'label': 'Press Release: James Dyson Foundation (PDF)'}],
  'images_after': [{'src': 'photos/vision-aerial-1.jpg',
                    'alt': "Architect's aerial view of the planned expansion: a crescent of new dark-timber "
                           'classrooms with coloured window frames around a central timber building, set in '
                           'gardens behind the existing school'},
                   {'src': 'photos/vision-aerial-2.jpg',
                    'alt': "Architect's aerial view from the car park side, showing the existing curved "
                           'school building with the new classroom buildings beyond it'},
                   {'src': 'photos/vision-ground-1.jpg',
                    'alt': "Architect's ground-level view of the new courtyard: dark-timber classrooms with "
                           'red and blue window frames, young trees and timber play features'},
                   {'src': 'photos/vision-ground-2.jpg',
                    'alt': "Architect's ground-level view across a wildflower meadow towards the new timber "
                           'building and classrooms'}]},
 {'src': 'about/results-2.md',
  'out': 'about/results/',
  'section': 'About',
  'title': 'Results',
  'portraits': {'RESULTS_CHART': {'src': 'photos/results-three-year-average.png',
                                  'cls': 'results-chart',
                                  'alt': 'Bar chart: average percentage of pupils meeting the expected '
                                         'standard in 2023-2025. School 71%, local authority state-funded '
                                         'schools 57%, England state-funded schools 61%.'}}},
 {'src': 'about/our-library.md',
  'out': 'about/our-library/',
  'section': 'Learning',
  'galleries': {'GALLERY_TOP': [{'src': 'library-display.jpg',
                                 'alt': 'Storyland Library display board',
                                 'caption': 'Welcome to the Storyland Library'},
                                {'src': 'photos/library-roald-dahl-display.jpg',
                                 'alt': 'Roald Dahl and dream jars reading display board'},
                                {'src': 'photos/library-bookshelf-display.jpg',
                                 'alt': 'Junior Library book shelf display'}],
                'GALLERY_BOOKS': [{'src': 'photos/library-have-you-read-board.jpg',
                                   'alt': 'Have you read...? bulletin board'},
                                  {'src': 'photos/library-guess-books-board.jpg',
                                   'alt': 'Can you guess the books? bulletin board'},
                                  {'src': 'photos/books-on-shelf.jpg',
                                   'alt': 'Illustration of a shelf of books'},
                                  {'src': 'photos/wimpy-kid.jpg',
                                   'alt': 'Diary of a Wimpy Kid book box set'}],
                'GALLERY_HISTORIES': [{'src': 'photos/library-horrible-histories-board.jpg',
                                       'alt': 'Horrible Histories display board'}]},
  'author_links': [{'name': 'Roald Dahl', 'href': 'http://www.roalddahl.com/home/kids'},
                   {'name': 'Eoin Colfer', 'href': 'http://www.eoincolfer.com/'},
                   {'name': 'Jeremy Strong', 'href': 'https://www.jeremystrong.co.uk/'},
                   {'name': 'Malorie Blackman', 'href': 'https://www.malorieblackman.co.uk/'},
                   {'name': 'Michael Morpurgo', 'href': 'https://www.michaelmorpurgo.com/'},
                   {'name': 'Sally Gardner', 'href': 'https://www.sallygardner.co.uk/'},
                   {'name': 'Dick King-Smith', 'href': 'http://www.dickkingsmith.com/'},
                   {'name': 'Angie Sage', 'href': 'http://www.angiesage.com/'}]},
 {'src': 'about/book-reviews.md', 'out': 'about/book-reviews/', 'section': 'Learning'},
 {'src': 'about/ofsted-report-2.md',
  'out': 'about/ofsted-report/',
  'section': 'About',
  'title': 'OFSTED & SIAMS Reports',
  'report_links': [{'href': 'https://files.ofsted.gov.uk/v1/file/50256444',
                    'icon': 'illustrations/report-icon-ofsted.svg',
                    'label': 'Read the Ofsted Report',
                    'text': 'Most recent inspection, May 2024. Opens in a new tab.'},
                   {'href': 'https://nse-school-reports.s3.eu-west-2.amazonaws.com/recpum0bZytD14M8W-report-siams-report-malmesbury-church-of-england-primary-school-139753-180526.pdf',
                    'icon': 'illustrations/report-icon-siams.svg',
                    'label': 'Read the SIAMS Report',
                    'text': 'Summer 2026 inspection. Opens in a new tab.'}]},
 {'src': 'about/governors.md',
  'out': 'about/governors/',
  'section': 'About',
  'governor_cards': GOVERNOR_CARDS},
 {'src': 'learning/online-learning-resources.md',
  'out': 'learning/online-learning-resources/',
  'section': 'Learning',
  'hidden': True},
 {'src': 'learning/curriculum.md',
  'out': 'learning/curriculum/',
  'section': 'Learning',
  'downloads': [{'href': 'Letter-about-helping-your-child-with-their-reading.pdf',
                 'label': 'Helping Your Child With Their Reading — Letter (PDF)'},
                {'href': 'Parent-Session-3-Spelling-power-point-Oct-2024.pdf',
                 'label': 'Parent Spelling Session, Oct 2024 (PDF)'},
                {'href': 'speed-read-speed-spell.pdf', 'label': 'Speed Read, Speed Spell (PDF)'},
                {'href': 'mnemonics-2.pdf', 'label': 'Spelling Mnemonics (PDF)'},
                {'href': 'Mnemonic-posters-for-spelling.pdf',
                 'label': 'Mnemonic Posters for Spelling (PDF)'}]},
 {'src': 'learning/marvellous-mathemagicians.md',
  'out': 'learning/maths-mastery/',
  'section': 'Learning',
  'title': 'Maths Mastery',
  'button_grids': {'GAMES_GRID': [[{'label': 'Click here for fun online maths games!',
                                    'href': '../maths-games/index.html',
                                    'color': 'purple'}],
                                  [{'image': 'photos/maths-illustration-numbers.svg', 'alt': ''}]],
                   'KEY_FEATURES_GRID': [[{'html': '<h2>Some Key features of this approach</h2><p>There will '
                                                   'be a significant amount of time devoted to developing '
                                                   'basic number concepts. This is to build up children’s '
                                                   'fluency as number awareness will affect their success in '
                                                   'other areas of mathematics. Children who are successful '
                                                   'with number are much more confident '
                                                   'mathematicians.</p>'}],
                                         [{'label': 'Download the Maths Mastery@Malmesbury presentation here',
                                           'href': '/documents/Maths-Mastery-presentation-Feb2020.pdf',
                                           'color': 'orange'},
                                          {'image': 'photos/maths-illustration-shapes.svg', 'alt': ''}]],
                   'CPA_GRID': [[{'html': '<h4>Concrete</h4><p>Children will have the opportunity to use '
                                          'concrete objects and manipulatives to help them understand what '
                                          'they are doing.</p>'}],
                                [{'html': '<h4>Pictorial</h4><p>Children will then build on this concrete '
                                          'approach by using pictorial representations. These '
                                          'representations can then be used to reason and solve '
                                          'problems.</p>'}],
                                [{'html': '<h4>Abstract</h4><p>With the foundations firmly laid, children '
                                          'will be able to move to an abstract approach using numbers and '
                                          'key concepts with confidence.</p>'}]]},
  'button_rows': {'NC_PROGRESSION_BUTTON': [{'label': 'National Curriculum Primary Progression: Maths',
                                             'href': '/documents/National-Curriculum-Progression-Primary-Maths.pdf',
                                             'color': 'purple'}],
                  'GOV_NC_BUTTON': [{'label': 'Maths National Curriculum',
                                     'href': 'https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/335158/PRIMARY_national_curriculum_-_Mathematics_220714.pdf',
                                     'color': 'blue',
                                     'external': True}]}},
 {'src': 'learning/maths-games.md',
  'out': 'learning/maths-games/',
  'section': 'Learning',
  'title': 'Maths Games to Play at Home',
  'button_rows': {'TTRS_BUTTON': [{'label': 'Log in to Times Tables Rock Stars',
                                   'href': 'https://ttrockstars.com/login',
                                   'color': 'blue',
                                   'external': True}],
                  'CHASE_BUTTON': [{'label': 'Try Maths Chase',
                                    'href': 'http://mathschase.com',
                                    'color': 'blue',
                                    'external': True}],
                  'HIT_BUTTON': [{'label': 'Go to Hit the Button',
                                  'href': 'https://www.topmarks.co.uk/maths-games/hit-the-button',
                                  'color': 'blue',
                                  'external': True}],
                  'TRANSUM_BUTTON': [{'label': 'Fast Factors times tables practice',
                                      'href': 'https://www.transum.org/Software/Fast_Factors/',
                                      'color': 'blue',
                                      'external': True}],
                  'BACK_BUTTON': [{'label': 'Back to Maths Mastery',
                                   'href': '../maths-mastery/index.html',
                                   'color': 'purple'}]}},
 {'src': 'learning/music-lessons.md', 'out': 'learning/music-lessons/', 'section': 'Learning'},
 {'src': 'learning/outdoor-learning.md',
  'out': 'learning/outdoor-learning/',
  'section': 'Learning',
  'photo_rows': {'OL_GROUNDS': [[('outdoor-01.jpg',
                                  "Trees and young saplings in the school's outdoor learning area"),
                                 ('outdoor-02.jpg', 'Polytunnel and wheelbarrow in the school garden')],
                                [('outdoor-03.jpg', 'Children sitting on log seats in the woodland area')]],
                 'OL_FIREPIT': [[('outdoor-05.jpg', 'Children toasting marshmallows over the firepit'),
                                 ('outdoor-04.jpg',
                                  'Children sitting round the firepit with an adult leader')]],
                 'OL_CHEF': [[('outdoor-06.jpg', 'Children preparing food at an outdoor table with a chef')]],
                 'OL_ECO': [[('outdoor-08.jpg', 'Compost bins and a wheelbarrow in the school grounds'),
                             ('outdoor-07.jpg', 'A water butt collecting rainwater from a shed roof')],
                            [('outdoor-09.jpg', 'Raised flower and vegetable beds beside the school field')]],
                 'OL_RHS': [[('outdoor-10.jpg',
                              "Children in red caps tending the school's wheelbarrow garden at the RHS show"),
                             ('outdoor-11.jpg',
                              "RHS Badminton Flower Show sign for Malmesbury C of E Primary School's "
                              'wheelbarrow, Our Historic Hilltop Town'),
                             ('outdoor-12.jpg', 'Clay hedgehogs and a Hedgehog Friendly Town sign')]],
                 'OL_CAMPING': [[('outdoor-13.jpg', 'Tents pitched on the school field'),
                                 ('outdoor-14.jpg', 'A row of wellington boots outside a tent')],
                                [('outdoor-15.jpg',
                                  'A nest made from sticks and feathers with a Welcome sign')]],
                 'OL_OUTDOORS': [[('outdoor-16.jpg', 'Two children hugging a tree'),
                                  ('outdoor-17.jpg', 'Children making bark rubbings and drawings outdoors')],
                                 [('outdoor-18.jpg', 'Children washing a doll in a water tray'),
                                  ('outdoor-19.jpg', 'Two children with pumpkins in a water tub'),
                                  ('outdoor-20.jpg', 'Children doing a water experiment on the playground')]],
                 'OL_ROAD': [[('outdoor-21.jpg',
                               'Children in high-visibility vests at a pedestrian crossing')]],
                 'OL_RIVER': [[('outdoor-22.jpg', 'Year 5 children by the river on a riverwalk'),
                               ('outdoor-23.jpg', 'Children sitting in a giant woven nest')]],
                 'OL_ABBEY': [[('outdoor-24.jpg', 'Children visiting the ruins of Malmesbury Abbey')]],
                 'OL_RESIDENTIAL': [[('outdoor-25.jpg',
                                      'Children in helmets and harnesses on a ropes activity'),
                                     ('outdoor-26.jpg', 'Children climbing a high ropes pole')],
                                    [('outdoor-27.jpg',
                                      'A group in wetsuits and buoyancy aids at the beach')]]}},
 {'src': 'learning/e-safety.md',
  'out': 'learning/e-safety/',
  'section': 'Learning',
  'title': 'Online Safety',
  'portraits': {'FOOTPRINT_IMAGE': {'src': 'photos/digital-footprint-illustration.svg',
                                    'cls': 'footprint-figure',
                                    'alt': 'Illustration of a footprint made of words such as photos, posts, '
                                           'searches, comments and location'}},
  'button_grids': {'TIPS_GRID_1': [[{'html': '<h4>Talk</h4><p>Take an interest in your child’s online world. '
                                             'Ask them to show you their favourite games, apps or '
                                             'videos.</p>'}],
                                   [{'html': '<h4>Check</h4><p>Know what apps, games and platforms your '
                                             'child is using and check the age rating before they start '
                                             'using something new.</p>'}],
                                   [{'html': '<h4>Set boundaries</h4><p>Agree some simple family rules about '
                                             'when, where and how devices are used.</p>'}]],
                   'TIPS_GRID_2': [[{'html': '<h4>Use parental controls</h4><p>These can help manage what '
                                             'children can access, but they are only one part of keeping '
                                             'children safe.</p>'}],
                                   [{'html': '<h4>Keep talking</h4><p>Don’t wait for something to go wrong '
                                             'before having conversations about online safety.</p>'}],
                                   [{'html': '<h4>Listen</h4><p>If your child tells you something has '
                                             'happened online, try not to panic or immediately take their '
                                             'device away. They need to know that they can come to you when '
                                             'something goes wrong.</p>'}]]},
  'button_rows': {'TALK_BUTTONS': [{'label': 'E-safety presentation slides',
                                    'href': '/documents/e-safety-talk-2021.pdf',
                                    'color': 'blue'},
                                   {'label': 'E-safety booklet',
                                    'href': '/documents/Online-safety-guide-for-parents.pdf',
                                    'color': 'blue'}],
                  'REEL_BUTTON': [{'label': 'Watch the first online safety reel on Instagram',
                                   'href': 'https://www.instagram.com/reels/DY4Ob6uKWzo6Gah1EkLXu3mRSBC1b8xONt-rJ80/',
                                   'color': 'purple',
                                   'external': True}]}},
 {'src': 'information/current-vacancies.md',
  'out': 'information/current-vacancies/',
  'section': 'Information',
  'button_rows': {'VAC_BANK_MDSA': [{'label': 'Further information and application form',
                                     'href': '/documents/Bank-MDSA-2026-27.zip',
                                     'color': 'navy'}],
                  'VAC_BANK_PITP': [{'label': 'Further information and application form',
                                     'href': '/documents/Bank-PITP-2025-26.zip',
                                     'color': 'navy'}]}},
 {'src': 'information/term-dates.md',
  'out': 'information/term-dates/',
  'section': 'Information',
  'downloads': [{'href': 'Term_Dates_2026_to_2027.pdf', 'label': 'Term Dates 2026-27 (PDF)'},
                {'href': 'MPS-Term-Dates-2027-2028.pdf', 'label': 'Term Dates 2027-28 (PDF)'}]},
 {'src': 'information/parents.md',
  'out': 'parents/',
  'section': 'Information',
  'title': 'Parents',
  'hidden': True,
  'images': [{'src': 'school-439-pixelated.jpg', 'alt': 'Children playing in the school playground'}]},
 {'src': 'information/admissions.md',
  'out': 'parents/admissions/',
  'section': 'Information > Parents',
  'dividers': {'STARTING_DIVIDER': 'Starting school',
               'OTHER_DIVIDER': 'Other information',
               'APPEALS_DIVIDER': 'Admission appeals',
               'FAQ_DIVIDER': 'Admissions FAQs'},
  'button_grids': {'POLICY_GRID': [[{'html': '<a class="map-consent" href="https://www.google.com/maps/d/viewer?mid=1dwyvDXrQHPtJJ-GHMtgdKWJ1GERmbBVn" target="_blank" rel="noopener" onclick="var f=document.createElement(\'iframe\');f.className=\'map-embed\';f.src=\'https://www.google.com/maps/d/embed?mid=1dwyvDXrQHPtJJ-GHMtgdKWJ1GERmbBVn\';f.title=\'Interactive map of the inner and outer designated areas\';this.replaceWith(f);return false;">Click to load Google map of the catchment area (uses Google cookies).</a>'}],
                                   [{'label': 'Admissions Arrangements 2026-2027',
                                     'href': '/documents/Admission-Policy-Malmesbury-CE-Primary-Academy-2026-27.pdf',
                                     'color': 'blue'},
                                    {'label': 'Admissions Arrangements 2027-2028',
                                     'href': '/documents/Admission-Policy-Malmesbury-CE-Primary-Academy-2027-28.pdf',
                                     'color': 'blue'},
                                    {'label': 'Map of Designated Areas',
                                     'href': '/images/photos/MPS-Inner-and-Outer-Designated-Areas.jpg',
                                     'color': 'blue',
                                     'needs': 'MPS-Inner-and-Outer-Designated-Areas.jpg'}]]},
  'button_rows': {'WILTS_ADMISSIONS_BUTTON': [{'label': 'Link to Wiltshire Council admissions page',
                                               'href': 'https://www.wiltshire.gov.uk/schools-learning-admissions-applying',
                                               'color': 'cyan'}],
                  'INDUCTION_BUTTON': [{'label': 'Induction guide for Reception children',
                                        'href': '/documents/Starting-School-Induction-Booklet.pdf',
                                        'color': 'blue'}],
                  'WILTS_FORMS_BUTTON': [{'label': 'Wiltshire Council Schools Admissions Forms',
                                          'href': 'https://www.wiltshire.gov.uk/schools-learning-forms-guides-policies',
                                          'color': 'blue'}]}},
 {'src': 'information/absence-school.md',
  'out': 'information/absence/',
  'section': 'Information',
  'title': 'Attendance and Absence',
  'button_rows': {'GUIDANCE_BUTTONS': [{'label': 'Detailed Absence Guidance',
                                        'href': '/documents/Guidance-for-parents-on-pupil-absence-Sept-2024.pdf',
                                        'color': 'blue'},
                                       {'label': 'Fixed Penalty Notices (Fines)',
                                        'href': '/documents/Parent-Leaflet-Penalty-Notices-for-Absence-from-School-July-2024.pdf',
                                        'color': 'blue'}],
                  'LEAVE_FORM_BUTTON': [{'label': 'Leave of Absence Request Form',
                                         'href': '/documents/Leave-of-Absence-Request-Form-MPS.pdf',
                                         'color': 'blue'}],
                  'DFE_BUTTON': [{'label': 'DfE information',
                                  'href': 'https://www.gov.uk/education/pupil-wellbeing-behaviour-and-attendance',
                                  'color': 'blue',
                                  'external': True}]}},
 {'src': 'information/school-lunches.md', 'out': 'parents/school-lunches/', 'section': 'Information'},
 {'src': 'information/school-uniform.md',
  'out': 'parents/school-uniform/',
  'section': 'Information',
  'images': [{'src': 'illustrations/uniform-flatlay.svg',
              'alt': 'Flat-lay illustration of school uniform items'}],
  'button_rows': {'UNIFORM_LINKS': [{'label': 'Acceptable styles',
                                     'href': '/documents/Uniform-Acceptable-and-Unacceptable-Examples.pdf',
                                     'color': 'maroon'},
                                    {'label': 'School Uniform Policy',
                                     'href': '/documents/School-uniform-policy.pdf',
                                     'color': 'navy'},
                                    {'label': 'Purchase uniform at our school shop',
                                     'href': 'http://malmesbury-church-of-england-primary-school.uk.arbor.sc',
                                     'color': 'green',
                                     'external': True},
                                    {'label': 'Scholars online shop',
                                     'href': 'https://scholars-uk.com/product-category/chippenham/primary-schools-chippenham/malmesbury-primary/',
                                     'color': 'orange',
                                     'external': True}],
                  'STIKINS_BUTTON': [{'label': 'Buy personalised name tags at Stikins',
                                      'href': 'https://www.stikins.co.uk/',
                                      'color': 'teal',
                                      'external': True}]},
  'inline_images': {'SHOES_IMAGE': {'src': 'photos/shoe-styles-2026.jpg',
                                    'alt': 'Chart of acceptable and unacceptable shoe styles',
                                    'caption': 'Acceptable shoe styles'},
                    'HAIR_IMAGE': {'src': 'photos/Hair-styles-1.jpg',
                                   'alt': 'Chart of acceptable and unacceptable hair styles',
                                   'caption': 'Acceptable hair styles'},
                    'JEWELLERY_IMAGE': {'src': 'photos/jewellery-styles.jpg',
                                        'alt': 'Chart of acceptable and unacceptable jewellery and hair '
                                               'accessories',
                                        'caption': 'Acceptable jewellery and hair accessories'},
                    'SMARTWATCH_IMAGE': {'src': 'illustrations/smartwatch-illustration.svg',
                                         'alt': 'Illustration of a smartwatch',
                                         'caption': None}},
  'figure_markers': {'SKIRTS_SHORTS_IMAGE': {'src': 'photos/Skirt-lengths.jpg',
                                             'alt': 'Chart of acceptable skirt and short lengths'}}},
 {'src': 'information/send-offer.md',
  'out': 'information/send-offer/',
  'section': 'Learning',
  'button_grids': {'SEND_TOP_GRID': [[{'label': 'Wiltshire Parent Carer Council',
                                       'href': 'https://www.wiltshireparentcarercouncil.co.uk/en/Home_Page',
                                       'color': 'blue',
                                       'external': True},
                                      {'label': 'Video: How the Parent Carer Council works',
                                       'href': 'https://www.youtube.com/watch?v=mixHNycerQE',
                                       'color': 'blue',
                                       'external': True},
                                      {'label': 'Wiltshire SENDIASS',
                                       'href': 'https://www.family-action.org.uk/what-we-do/children-families/wiltshire-sendiass/',
                                       'color': 'blue',
                                       'external': True}],
                                     [{'label': 'Malmesbury CE Primary SEND Information Report',
                                       'href': '/documents/SEN-Information-Report-document-September-2026.pdf',
                                       'color': 'blue'},
                                      {'label': 'Intent, Implementation and Impact Statement',
                                       'href': '/documents/3-Is-SEND-March-2023.pdf',
                                       'color': 'cyan'}]],
                   'REFORMS_GRID': [[{'text': 'The upcoming SEND reforms are explained in the video below, '
                                              'by a Wiltshire Councillor.'},
                                     {'label': 'SEND reforms - Jon Hubbard',
                                      'href': 'https://www.youtube.com/watch?v=pETZ2EmD0Nw',
                                      'color': 'cyan',
                                      'external': True}],
                                    [{'text': 'Click the link below to understand what impact the SEND '
                                              'reforms will have locally.'},
                                     {'label': 'Wiltshire SEND reforms - what this means for your child',
                                      'href': 'https://www.wiltshire.gov.uk/local-offer/news/SEND-Reform-what-this-means-for-you-and-your-child',
                                      'color': 'cyan',
                                      'external': True}]],
                   'COURSES_GRID': [[{'label': 'Course information',
                                      'href': 'https://www.wiltshire.gov.uk/local-offer/SMNYP',
                                      'color': 'cyan',
                                      'external': True},
                                     {'label': 'Wiltshire OAP (Ordinarily Available Provision)',
                                      'href': 'https://www.wiltshire.gov.uk/article/8135/Section-One-Partnership-with-parents-carers-and-young-people',
                                      'color': 'cyan',
                                      'external': True}],
                                    [{'image': 'photos/wiltshire-local-offer.png',
                                      'alt': 'Wiltshire Local Offer website',
                                      'href': 'http://www.wiltshire.gov.uk/local-offer',
                                      'external': True}]],
                   'USEFUL_GRID': [[{'label': 'National Autistic Society',
                                     'href': 'https://www.autism.org.uk/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'The National ADD Information and Support Service',
                                     'href': 'http://addiss.co.uk/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'The Dyspraxia Foundation',
                                     'href': 'https://dyspraxiafoundation.org.uk/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'The British Epilepsy Association',
                                     'href': 'https://www.epilepsy.org.uk/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'World Autism Awareness Week: Primary School Resources 1',
                                     'href': '/documents/World-Autism-Awareness-Week-Primary-school-learning-resources.mp4',
                                     'color': 'blue',
                                     'needs_doc': 'World-Autism-Awareness-Week-Primary-school-learning-resources.mp4'}],
                                   [{'label': 'Autism Independent UK',
                                     'href': 'https://autismuk.com/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'RNIB: Education and Learning Tools for Visually Impaired '
                                              'Children',
                                     'href': 'https://www.rnib.org.uk/living-with-sight-loss/education-and-learning/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'Royal Institute for the Blind',
                                     'href': 'https://www.rnib.org.uk/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'Tourette Syndrome (UK) Association',
                                     'href': 'https://www.tourettes-action.org.uk/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'World Autism Awareness Week: Primary School Resources 2',
                                     'href': '/documents/World-Autism-Awareness-Week-Primary-school-learning-resources_2.mp4',
                                     'color': 'blue',
                                     'needs_doc': 'World-Autism-Awareness-Week-Primary-school-learning-resources_2.mp4'}],
                                   [{'label': 'British Dyslexia Association',
                                     'href': 'https://www.bdadyslexia.org.uk/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'National Deaf Children’s Society',
                                     'href': 'https://www.ndcs.org.uk/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'OCD UK',
                                     'href': 'https://www.ocduk.org/',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'Useful autism video',
                                     'href': 'https://www.youtube.com/watch?v=VAogdfYPstU',
                                     'color': 'blue',
                                     'external': True},
                                    {'label': 'Autism Information session March 2022',
                                     'href': 'https://youtu.be/wz0wZBQat-s',
                                     'color': 'purple',
                                     'external': True},
                                    {'label': 'Autism Acceptance Month 2026',
                                     'href': '/documents/Parent-Information-Autism-Acceptance-Month-April-2026.pdf',
                                     'color': 'purple'}]],
                   'EPILEPSY_GRID': [[{'text': 'Epilepsy Awareness Day usually falls in March. Click the '
                                               'link to the British Epilepsy Association (above) for further '
                                               'information, and take a look at the videos below:'},
                                      {'label': 'Epilepsy video for KS1 (Yrs 0-2)',
                                       'href': 'https://learn.epilepsy.org.uk/wp-content/uploads/classroon-resources/Spike-and-me/story.html',
                                       'color': 'blue',
                                       'external': True},
                                      {'label': 'Epilepsy video for KS2 (Yrs 3-6)',
                                       'href': 'https://learn.epilepsy.org.uk/wp-content/uploads/classroon-resources/All-about-epilepsy/story.html',
                                       'color': 'blue',
                                       'external': True}],
                                     [{'image': 'photos/Epilepsy-300x255.jpg',
                                       'alt': 'Illustration of a human head with brain and nerve '
                                              'connections'}]]},
  'button_rows': {'POLICIES_BUTTON': [{'label': 'Click for our policies page',
                                       'href': '/information/policies-and-statements/index.html',
                                       'color': 'blue'}],
                  'AUTISM_PACK_BUTTON': [{'label': 'Download information pack',
                                          'href': 'http://www.wiltshireparentcarercouncil.co.uk/en/Signposting_-_Health_%26_wellbeing_-_Specific_conditions_-_The_Wiltshire_Autism_Information_Pack',
                                          'color': 'blue',
                                          'external': True}]}},
 {'src': 'information/dyslexia-friendly-schools-project.md',
  'out': 'information/dyslexia-friendly-schools/',
  'section': 'Learning',
  'title': 'Dyslexia Friendly Schools',
  'dividers': {'WILTSHIRE_DIVIDER': 'Dyslexia in Wiltshire 2022',
               'MINDMAP_DIVIDER': 'Dyslexia Mind Map',
               'INFO_DIVIDER': 'Dyslexia Information',
               'TIPS_DIVIDER': 'TOP TIPS',
               'READING_DIVIDER': 'Enjoying Reading with Dyslexia'},
  'button_rows': {'WILTSHIRE_BUTTON': [{'label': 'Dyslexia in Wiltshire - latest information from Wiltshire '
                                                 'Council',
                                        'href': '/documents/Dyslexia-in-Wiltshire-2022.pdf',
                                        'color': 'orange'}]},
  'button_grids': {'RESOURCES_GRID_2': [[{'label': 'A Handy Little Guide to Dyslexia',
                                          'href': '/documents/handy-little-guide-to-dyslexia.pdf',
                                          'color': 'green'},
                                         {'label': 'The 100 most important words for children to learn to '
                                                   'read and spell (BBC article)',
                                          'href': 'http://news.bbc.co.uk/1/hi/education/4514106.stm',
                                          'color': 'green',
                                          'external': True}],
                                        [{'label': 'DAW24 Parent and Carer Information Pack',
                                          'href': '/documents/DAW24ParentandCarerInformationPack.pdf',
                                          'color': 'blue'},
                                         {'label': 'Dyslexia presentation slides - 9 October 2024',
                                          'href': '/documents/Parent-Session-3-Spelling-power-point-Oct-2024.pdf',
                                          'color': 'orange'}]],
                   'RESOURCES_GRID_3': [[{'image': 'photos/221_BDA-quality_mark_C_RGB.jpg',
                                          'alt': 'British Dyslexia Association Dyslexia Friendly quality '
                                                 'mark',
                                          'href': 'https://www.bdadyslexia.org.uk/advice/educators/creating-a-dyslexia-friendly-school/dyslexia-friendly-school-awards',
                                          'external': True},
                                         {'label': 'Malmesbury Primary awarded Dyslexia Quality Mark',
                                          'href': '/documents/Malmesbury-and-Lyneham-Schools-in-Contact-Mag.pdf',
                                          'color': 'cyan'}],
                                        [{'label': 'Mnemonic posters for spelling help',
                                          'href': '/documents/Mnemonic-posters-for-spelling.pdf',
                                          'color': 'blue'},
                                         {'label': 'More mnemonics for spelling',
                                          'href': '/documents/mnemonics-2.pdf',
                                          'color': 'blue'},
                                         {'label': 'Speed read speed spell',
                                          'href': '/documents/speed-read-speed-spell.pdf',
                                          'color': 'blue'},
                                         {'label': 'Dyslexia and SpLD friendly protocol',
                                          'href': '/documents/Dyslexia-Friendly-Protocol-July-2021.pdf',
                                          'color': 'blue'}],
                                        [{'label': 'Dyslexia presentation - 5th October 2023',
                                          'href': 'https://www.youtube.com/watch?v=oy07tzjwbsY',
                                          'color': 'purple',
                                          'external': True},
                                         {'label': 'Dyslexia presentation - 22nd November 2022',
                                          'href': 'https://malmesburyprimary-my.sharepoint.com/:v:/g/personal/lauraphillips_malmesbury-pri_wilts_sch_uk/Ec2YDswAMqFGvdGss0U0UAsBluRMHA7yrAf4pwIHgWfBKg',
                                          'color': 'purple',
                                          'external': True},
                                         {'label': 'Dyslexia presentation - 5th October 2021',
                                          'href': 'https://malmesburyprimary-my.sharepoint.com/:v:/g/personal/lauraphillips_malmesbury-pri_wilts_sch_uk/EYgHWnyIJ35HvjXoXwxdZfMBGNlTfclK25iByE-8XJEdOg',
                                          'color': 'purple',
                                          'external': True}]],
                   'MINDMAP_GRID': [[{'image': 'photos/dyslexia-mind-map.jpg', 'alt': 'Dyslexia mind map'}]],
                   'INFO_GRID': [[{'label': 'See Dyslexia Differently (video)',
                                   'href': '/documents/See-dyslexia-differently-video-1.mp4',
                                   'color': 'blue',
                                   'external': True}],
                                 [{'label': 'Empowered Parents Pack (Link to the BDA)',
                                   'href': 'https://cdn.bdadyslexia.org.uk/documents/Empowered-Parents.pdf',
                                   'color': 'blue',
                                   'external': True}]],
                   'TIPS_GRID': [[{'image': 'photos/Tricky-spellings.jpg',
                                   'alt': 'Tricky spellings factsheet cover',
                                   'href': '/documents/Dyslexia-Information-For-Parents-Spelling-Factsheet.pdf'},
                                  {'label': 'Spelling factsheet',
                                   'href': '/documents/Dyslexia-Information-For-Parents-Spelling-Factsheet.pdf',
                                   'color': 'coral'},
                                  {'image': 'photos/Love-literacy.jpg',
                                   'alt': 'Love literacy factsheet cover',
                                   'href': '/documents/Dyslexia-Information-For-Parents-Literacy-Factsheet.pdf'},
                                  {'label': 'Literacy factsheet',
                                   'href': '/documents/Dyslexia-Information-For-Parents-Literacy-Factsheet.pdf',
                                   'color': 'coral'}],
                                 [{'image': 'photos/Home-support.jpg',
                                   'alt': 'Home support factsheet cover',
                                   'href': '/documents/Dyslexia-Information-For-Parents-October-2022.pdf'},
                                  {'label': 'Home support factsheet',
                                   'href': '/documents/Dyslexia-Information-For-Parents-October-2022.pdf',
                                   'color': 'coral'},
                                  {'image': 'photos/Shine-at-Maths.jpg',
                                   'alt': 'Shine at maths factsheet cover',
                                   'href': '/documents/Dyslexia-Information-For-Parents-Maths-Factsheet.pdf'},
                                  {'label': 'Maths factsheet',
                                   'href': '/documents/Dyslexia-Information-For-Parents-Maths-Factsheet.pdf',
                                   'color': 'coral'}]],
                   'READING_GRID': [[{'image': 'photos/Dive-In-cover-1.jpg',
                                      'alt': 'Cover of Dive In! A guide to dyslexia-friendly reading books',
                                      'href': '/documents/Dive_In_-A-Dyslexia-Friendly-Book-Guide_2017031-Copy.pdf'}],
                                    [{'text': 'This guide has some suggestions for books you might like to '
                                              'try.'},
                                     {'label': 'Dive In! A guide to dyslexia-friendly reading books',
                                      'href': '/documents/Dive_In_-A-Dyslexia-Friendly-Book-Guide_2017031-Copy.pdf',
                                      'color': 'blue'},
                                     {'image': 'photos/books-for-dyslexia.jpg',
                                      'alt': 'Books for dyslexic readers'}]],
                   'SUPERPOWER_GRID': [[{'label': 'Video: Dyslexia is my Superpower',
                                         'href': 'https://www.youtube.com/watch?v=Tya0HJpuyeg',
                                         'color': 'blue',
                                         'external': True}],
                                       [{'image': 'photos/Dyslexia-pic.jpg',
                                         'alt': "Still from the video 'Dyslexia is my Superpower'",
                                         'href': 'https://www.youtube.com/watch?v=Tya0HJpuyeg',
                                         'external': True}]],
                   'MADEBY_GRID': [[{'image': 'photos/made-by-dyslexia-300x300.jpg',
                                     'alt': 'Made by Dyslexia logo',
                                     'href': '/documents/Made-By-Dyslexia-Information-Video.mp4',
                                     'external': True}],
                                   [{'text': 'Click on the button below to view a video by the global '
                                             'charity ‘Made by Dyslexia’. The campaign is led by successful '
                                             'dyslexics, with the aim of helping the world to understand, '
                                             'value and support dyslexia.'},
                                    {'label': 'Made by Dyslexia',
                                     'href': '/documents/Made-By-Dyslexia-Information-Video.mp4',
                                     'color': 'blue',
                                     'external': True}]],
                   'SPELLINGFUN_GRID': [[{'label': 'Making spelling fun',
                                          'href': 'https://www.readandspell.com/making-spelling-fun',
                                          'color': 'blue',
                                          'external': True}],
                                        [{'image': 'photos/Spelling-Fun.jpg',
                                          'alt': 'Making spelling fun'}]]}},
 {'src': 'information/policies-and-statements.md',
  'out': 'information/policies-and-statements/',
  'section': 'Information'},
 {'src': 'information/pupil-premium-statement.md',
  'out': 'information/pupil-premium-statement/',
  'section': 'Information',
  'button_rows': {'PP_BUTTON': [{'label': 'Pupil Premium Strategy Statement 2025–2028',
                                 'href': '/documents/Pupil_premium_strategy_statement-2025.docx',
                                 'color': 'navy'}]}},
 {'src': 'information/pe-grant-statement.md',
  'out': 'information/pe-grant-statement/',
  'section': 'Information',
  'title': 'PE and Sport Premium'},
 {'src': 'information/academy-information.md',
  'out': 'information/academy-information/',
  'section': 'Information',
  'button_rows': {'ACADEMY_BUTTONS': [{'label': 'Annual Accounts and Trustees Report 2024‑25',
                                       'href': '/documents/Final-accounts-24-25.pdf',
                                       'color': 'navy'},
                                      {'label': 'Funding Agreement',
                                       'href': '/documents/Funding-Agreement-Malmesbury-CofE-Primary.pdf',
                                       'color': 'teal'},
                                      {'label': 'Memorandum of Association',
                                       'href': '/documents/Memorandum-of-Association-Malmesbury-CofE-Primary.pdf',
                                       'color': 'blue'},
                                      {'label': 'Articles of Association',
                                       'href': '/documents/Malmesbury-CofE-Articles-of-Association.pdf',
                                       'color': 'green'},
                                      {'label': 'Scheme of Delegation 2026‑27',
                                       'href': '/documents/MPS-Scheme-of-Delegation-2026-27.pdf',
                                       'color': 'purple'}]}},
 {'src': 'information/british-values.md',
  'out': 'information/british-values/',
  'section': 'Information',
  'hidden': True},
 {'src': 'classes/eyfs.md',
  'out': 'classes/eyfs/',
  'section': 'Classes',
  'button_rows': {'MEET_TEACHER_BUTTON': [{'label': 'Meet the Teacher presentation Sept 2026',
                                           'href': '/documents/EYFS_Meet-the-teacher.pdf',
                                           'color': 'blue'}],
                  'PRESENTATIONS_BUTTONS': [{'label': 'Induction booklet 2025_26',
                                             'href': '/documents/Starting-School-Induction-Booklet.pdf',
                                             'color': 'navy'},
                                            {'label': 'Phonics',
                                             'href': '/documents/Phonics-presentation.pdf',
                                             'color': 'teal'}],
                  'OVERVIEW_BUTTON': [{'label': 'Curriculum overview for the year',
                                       'href': '/documents/Curriculum-Topic-Overview-2026-27.pdf',
                                       'color': 'blue'}],
                  'POLICY_BUTTONS': [{'label': 'EYFS policy',
                                      'href': '/documents/EYFS-Policy-March-2026.pdf',
                                      'color': 'green'},
                                     {'label': 'EYFS curriculum statement',
                                      'href': '/documents/EYFS-curriculum-outline.pdf',
                                      'color': 'green'}],
                  'SUBJECTS_BUTTONS': [{'label': 'Communication and Language',
                                        'href': '/documents/Communication-and-Language-1.pdf',
                                        'color': 'blue'},
                                       {'label': 'Physical Development',
                                        'href': '/documents/Physical-Development.pdf',
                                        'color': 'blue'},
                                       {'label': 'PSED', 'href': '/documents/PSED.pdf', 'color': 'blue'},
                                       {'label': 'Literacy',
                                        'href': '/documents/Literacy.pdf',
                                        'color': 'blue'},
                                       {'label': 'Understanding the World',
                                        'href': '/documents/Understanding-the-World.pdf',
                                        'color': 'blue'},
                                       {'label': 'Mathematics',
                                        'href': '/documents/Mathematics.pdf',
                                        'color': 'blue'},
                                       {'label': 'Expressive Arts and Design',
                                        'href': '/documents/Expressive-Arts-and-Design.pdf',
                                        'color': 'blue'}]},
  'dividers': {'PRESENTATIONS_DIVIDER': 'Presentations',
               'NEWSLETTERS_DIVIDER': 'Curriculum newsletters',
               'CURRICULUM2023_DIVIDER': 'Our Curriculum'},
  'image_button_rows': {'NEWSLETTERS_ROW': {'image': {'src': 'photos/playing_children_02.jpg',
                                                      'alt': 'Cartoon clip-art pattern of children playing'},
                                            'buttons': [{'label': 'Term 1 Homework Grid',
                                                         'href': '/documents/T1_EYFS_Homework.pdf',
                                                         'color': 'orange'},
                                                        {'label': 'Term 1: All About Me',
                                                         'href': '/documents/T1_EYFS_All-about-me.pdf',
                                                         'color': 'blue'},
                                                        {'label': 'Term 2 Homework Grid',
                                                         'href': '/documents/T2_EYFS_Homework.pdf',
                                                         'color': 'green'},
                                                        {'label': "Term 2: Let's Celebrate",
                                                         'href': '/documents/T2_EYFS_Lets-Celebrate.pdf',
                                                         'color': 'purple'}],
                                            'image_first': True}}},
 {'src': 'classes/year-1.md',
  'out': 'classes/year-1/',
  'section': 'Classes',
  'button_rows': {'PRESENTATIONS_BUTTONS': [{'label': 'Click for our Meet the Teacher presentation (2026/27)',
                                             'href': '/documents/Y1_MeetTheTeacher2026.pdf',
                                             'color': 'orange'},
                                            {'label': 'Transition into Year 1 presentation June 2026',
                                             'href': '/documents/Transition-into-Year-1-presentation-June-2026.pdf',
                                             'color': 'green'},
                                            {'label': 'Little Wandle Presentation',
                                             'href': '/documents/Little-Wandle-Presentation.pdf',
                                             'color': 'purple'}],
                  'OVERVIEW_BUTTONS': [{'label': 'Detailed Curriculum',
                                        'href': '/documents/MPS-curriculum-Year-1.pdf',
                                        'color': 'green'},
                                       {'label': 'Curriculum Overview',
                                        'href': '/documents/Curriculum-Topic-Overview-2026-27.pdf',
                                        'color': 'green'}]},
  'dividers': {'NEWSLETTERS_DIVIDER': 'Year 1 curriculum newsletters',
               'HOMEWORK_DIVIDER': 'Homework information',
               'OVERVIEW_DIVIDER': 'Year 1 curriculum overview'},
  'image_button_rows': {'NEWSLETTERS_ROW': {'image': {'src': 'photos/T2-Y1-toys.jpg',
                                                      'alt': "Colourful clip-art collection of children's "
                                                             'toys'},
                                            'buttons': [{'label': 'Term 1 Homework',
                                                         'href': '/documents/T1_Y1_Homework.pdf',
                                                         'color': 'orange'},
                                                        {'label': 'Term 1: We are what we eat',
                                                         'href': '/documents/T1_Y1_-We-are-what-we-eat-2026.pdf',
                                                         'color': 'blue'},
                                                        {'label': 'Term 2 Homework',
                                                         'href': '/documents/T2_Y1_Homework.pdf',
                                                         'color': 'green'},
                                                        {'label': 'Term 2: Toys',
                                                         'href': '/documents/T2_Y1_Toys.pdf',
                                                         'color': 'purple'}],
                                            'image_first': True},
                        'HOMEWORK_ROW': {'image': {'src': 'photos/Y1-hwk-poster.jpg',
                                                   'alt': 'Year 1 Homework Guide poster showing the weekly '
                                                          'homework routine'},
                                         'buttons': [{'label': 'Homework Timetable poster',
                                                      'href': '/documents/homework-poster.pdf',
                                                      'color': 'blue'}],
                                         'image_first': False}}},
 {'src': 'classes/year-2.md',
  'out': 'classes/year-2/',
  'section': 'Classes',
  'button_rows': {'WANDLE_BUTTON': [{'label': 'Little Wandle Presentation',
                                     'href': '/documents/LS-PowerPoint-for-parents-presentation-September-2022-1.pptx',
                                     'color': 'purple'}],
                  'OVERVIEW_BUTTONS': [{'label': 'Detailed Curriculum',
                                        'href': '/documents/MPS-curriculum-Year-2.pdf',
                                        'color': 'green'},
                                       {'label': 'Curriculum Overview',
                                        'href': '/documents/Curriculum-Topic-Overview-2026-27.pdf',
                                        'color': 'green'}]},
  'dividers': {'WANDLE_DIVIDER': 'Little Wandle',
               'NEWSLETTERS_DIVIDER': 'Year 2 curriculum newsletters and homework tasks',
               'OVERVIEW_DIVIDER': 'Year 2 curriculum overview'},
  'image_button_rows': {'NEWSLETTERS_ROW': {'image': {'src': 'photos/T2-Y2-fireworks.jpg',
                                                      'alt': 'Colourful fireworks bursting in the night sky'},
                                            'buttons': [{'label': 'Term 1: Homework grid',
                                                         'href': '/documents/T1_Y2_homework.pdf',
                                                         'color': 'orange'},
                                                        {'label': 'Term 1: The Victorians',
                                                         'href': '/documents/T1_Y2_The-Victorians.pdf',
                                                         'color': 'blue'},
                                                        {'label': 'Term 2: Homework grid',
                                                         'href': '/documents/T2_Y2_Homework.pdf',
                                                         'color': 'green'},
                                                        {'label': 'Term 2: Celebrations',
                                                         'href': '/documents/T2_Y2_Celebrations.pdf',
                                                         'color': 'purple'}],
                                            'image_first': False}}},
 {'src': 'classes/year-3.md',
  'out': 'classes/year-3/',
  'section': 'Classes',
  'button_rows': {'MEET_TEACHER_BUTTON': [{'label': 'Meet the Teacher presentation (Sept 2026)',
                                           'href': '/documents/Y3_Meet-the-Teacher_2026.pdf',
                                           'color': 'blue'}],
                  'OVERVIEW_BUTTON': [{'label': 'Curriculum Overview',
                                       'href': '/documents/Curriculum-Topic-Overview-2026-27.pdf',
                                       'color': 'green'}]},
  'dividers': {'NEWSLETTERS_DIVIDER': 'Year 3 curriculum newsletters',
               'OVERVIEW_DIVIDER': 'Year 3 curriculum overview'},
  'image_button_rows': {'NEWSLETTERS_ROW': {'image': {'src': 'photos/T2-MP2-volcano.jpg',
                                                      'alt': 'Volcano erupting with glowing lava at dusk'},
                                            'buttons': [{'label': 'Term 1 Homework',
                                                         'href': '/documents/T1_MP2_homework.pdf',
                                                         'color': 'orange'},
                                                        {'label': 'Term 1: Temples, Tombs and Treasures',
                                                         'href': '/documents/T1_MP2_Temples-TombsTreasures.pdf',
                                                         'color': 'blue'},
                                                        {'label': 'Term 2: Active Planet',
                                                         'href': '/documents/T2_MP2_Active-Planet.pdf',
                                                         'color': 'purple'}],
                                            'image_first': False}}},
 {'src': 'classes/year-4.md',
  'out': 'classes/year-4/',
  'section': 'Classes',
  'button_rows': {'MEET_TEACHER_BUTTON': [{'label': 'Meet the Teachers (Sept 2026)',
                                           'href': '/documents/Y4_Meet-the-teacher_26_27.pdf',
                                           'color': 'orange'}],
                  'GRITTLETON_BUTTONS': [{'label': 'Presentation about our 2025 Grittleton trip',
                                          'href': '/documents/Grittleton-parent-presentation-pixelated.pdf',
                                          'color': 'navy'},
                                         {'label': 'Recommended kit list',
                                          'href': '/documents/Grittleton-Adventures-Recommended-Kit-List.pdf',
                                          'color': 'orange'}],
                  'READING_BUTTONS': [{'label': 'Year 4 letter about reading',
                                       'href': '/documents/Letter-about-helping-your-child-with-their-reading.pdf',
                                       'color': 'blue'},
                                      {'label': 'Recommended reading list',
                                       'href': '/documents/Recommended_books_for_Year_4-.pdf',
                                       'color': 'blue'},
                                      {'label': 'Reading Rockets website',
                                       'href': 'https://www.readingrockets.org/books',
                                       'color': 'blue',
                                       'external': True}],
                  'OVERVIEW_BUTTON': [{'label': 'Curriculum Overview',
                                       'href': '/documents/Curriculum-Topic-Overview-2026-27.pdf',
                                       'color': 'green'}]},
  'dividers': {'MEET_TEACHER_DIVIDER': 'Year 4 Meet the Teacher presentation',
               'NEWSLETTERS_DIVIDER': 'Year 4 curriculum newsletters',
               'GRITTLETON_DIVIDER': 'Grittleton Residential',
               'READING_DIVIDER': 'Help your child with reading',
               'OVERVIEW_DIVIDER': 'Year 4 curriculum overview'},
  'image_button_rows': {'NEWSLETTERS_ROW': {'image': {'src': 'photos/T2-MP2-volcano.jpg',
                                                      'alt': 'Volcano erupting with glowing lava at dusk'},
                                            'buttons': [{'label': 'Term 1 Homework',
                                                         'href': '/documents/T1_MP2_homework.pdf',
                                                         'color': 'orange'},
                                                        {'label': 'Term 1: Temples, Tombs and Treasure',
                                                         'href': '/documents/T1_MP2_Temples-TombsTreasures.pdf',
                                                         'color': 'blue'},
                                                        {'label': 'Term 2: Active Planet',
                                                         'href': '/documents/T2_MP2_Active-Planet.pdf',
                                                         'color': 'purple'}],
                                            'image_first': False}},
  'figure_markers': {'GRITTLETON_IMAGE': {'src': 'photos/Grittleton-House.jpg',
                                          'alt': 'Exterior photo of Grittleton House, the residential trip '
                                                 'venue'}}},
 {'src': 'classes/year-5.md',
  'out': 'classes/year-5/',
  'section': 'Classes',
  'button_rows': {'WELCOME_BUTTON': [{'label': "Click here for our 'Meet the Teachers: Welcome to Year 5' "
                                               'presentation (2026/27)',
                                      'href': '/documents/Y5_Meet-the-teacher_26_27.pdf',
                                      'color': 'orange'}],
                  'READING_LIST_BUTTON': [{'label': 'Year 5 Recommended Reading List',
                                           'href': '/documents/Year-5-Recommended-Reads.pdf',
                                           'color': 'teal'}],
                  'OVERVIEW_BUTTON': [{'label': 'Curriculum Overview',
                                       'href': '/documents/Curriculum-Topic-Overview-2026-27.pdf',
                                       'color': 'green'}]},
  'dividers': {'WELCOME_DIVIDER': 'Welcome to Year 5 presentation',
               'HOMEWORK_READING_DIVIDER': 'Homework and reading information',
               'NEWSLETTERS_DIVIDER': 'Year 5 curriculum newsletters',
               'OVERVIEW_DIVIDER': 'Year 5 curriculum overview'},
  'image_button_rows': {'NEWSLETTERS_ROW': {'image': {'src': 'photos/T2-MP3-evacuees.jpg',
                                                      'alt': 'Cartoon of two wartime evacuee children with '
                                                             'luggage and labels'},
                                            'buttons': [{'label': 'Homework Term 1',
                                                         'href': '/documents/T1_MP3_homework.pdf',
                                                         'color': 'orange'},
                                                        {'label': 'Term 1 newsletter: Space Explorers',
                                                         'href': '/documents/T1_MP3_Space-Explorers.pdf',
                                                         'color': 'blue'},
                                                        {'label': 'Homework Term 2',
                                                         'href': '/documents/T2_MP3_homework.pdf',
                                                         'color': 'green'},
                                                        {'label': 'Term 2 newsletter: Lest We Forget',
                                                         'href': '/documents/T2_MP3_Lest-We-Forget.pdf',
                                                         'color': 'purple'}],
                                            'image_first': False}}},
 {'src': 'classes/year-6.md',
  'out': 'classes/year-6/',
  'section': 'Classes',
  'button_rows': {'OVERVIEW_BUTTON': [{'label': 'Curriculum Overview',
                                       'href': '/documents/Curriculum-Topic-Overview-2026-27.pdf',
                                       'color': 'green'}]},
  'dividers': {'NEWSLETTERS_DIVIDER': 'Year 6 curriculum newsletters',
               'MORFA_DIVIDER': 'Morfa Bay',
               'OVERVIEW_DIVIDER': 'Year 6 curriculum overview'},
  'image_button_rows': {'NEWSLETTERS_ROW': {'image': {'src': 'photos/T2-MP3-evacuees.jpg',
                                                      'alt': 'Cartoon of two wartime evacuee children with '
                                                             'luggage and labels'},
                                            'buttons': [{'label': 'Homework Term 1',
                                                         'href': '/documents/T1_MP3_homework.pdf',
                                                         'color': 'teal'},
                                                        {'label': 'Term 1 newsletter: Space Explorers',
                                                         'href': '/documents/T1_MP3_Space-Explorers.pdf',
                                                         'color': 'blue'},
                                                        {'label': 'Homework Term 2',
                                                         'href': '/documents/T2_MP3_homework.pdf',
                                                         'color': 'green'},
                                                        {'label': 'Term 2 newsletter: Lest We Forget',
                                                         'href': '/documents/T2_MP3_Lest-We-Forget.pdf',
                                                         'color': 'purple'}],
                                            'image_first': False},
                        'MORFA_ROW': {'image': {'src': 'photos/accommodation.jpg',
                                                'alt': 'Exterior photo of the Morfa Bay residential '
                                                       'accommodation buildings and picnic area'},
                                      'buttons': [{'label': 'Morfa Bay Information Evening Slides for 2027 '
                                                            'trip',
                                                   'href': '/documents/Morfa-Bay-June-2027-pixelated.pdf',
                                                   'color': 'blue'},
                                                  {'label': 'Morfa Bay Kit List',
                                                   'href': '/documents/Kit-List-MORFA-BAY.pdf',
                                                   'color': 'blue'}],
                                      'image_first': True}}},
 {'src': 'classes/homework.md',
  'out': 'classes/homework/',
  'section': 'Classes',
  'hidden': True,
  'downloads': [{'href': 'T1_MP3_homework.pdf', 'label': 'Term 1 Milepost 3 (Years 5-6) Homework (PDF)'}]},
 {'src': 'travel/travel.md', 'out': 'travel/', 'section': 'Travel'},
 {'src': 'safeguarding/safeguarding.md',
  'out': 'safeguarding/',
  'section': 'Safeguarding',
  'person_cards': {'DSL_CARDS': [{'photo': 'photos/gov-stephen-heal.jpg',
                                  'name': 'Steve Heal',
                                  'role': 'Head Teacher'},
                                 {'photo': 'photos/gov-jonathan-watkins.jpg',
                                  'name': 'Jonathan Watkins',
                                  'role': 'Deputy Head Teacher'}]},
  'button_rows': {'POLICY_BUTTON': [{'label': 'Safeguarding and Child Protection Policy',
                                     'color': 'maroon',
                                     'href': '/documents/Safeguarding-and-Child-Protection-Policy-Oct-2026.pdf'}]}},
 {'src': 'other/contact.md',
  'out': 'contact/',
  'section': 'Contact',
  'tabs': {'CONTACT_TABS': [{'label': 'Write',
                             'image': 'photos/IMG_3204-1.jpg',
                             'alt': 'Malmesbury C of E Primary School building, with a sign giving the '
                                    'school address',
                             'html': '<p class="tab-address">Malmesbury C of E Primary School<br>Tetbury '
                                     'Hill<br>Malmesbury<br>Wiltshire<br>SN16 9JR</p>'},
                            {'label': 'Call',
                             'html': '<p>Should you wish to speak to somebody at the school urgently our '
                                     'phone number is <a href="tel:+441666823514">(01666) 823514</a>.</p>'},
                            {'label': 'Email',
                             'html': '<p>General enquiries are dealt with by Emma Grayson and should be sent '
                                     'to <a '
                                     'href="mailto:admin@malmesbury-pri.wilts.sch.uk">admin@malmesbury-pri.wilts.sch.uk</a></p><p>Any '
                                     'financial/payment/accounting issues should be directed to <a '
                                     'href="mailto:finance@malmesbury-pri.wilts.sch.uk">finance@malmesbury-pri.wilts.sch.uk</a></p>'}]}},
 {'src': 'other/payments.md',
  'out': 'payments/',
  'section': 'Information',
  'button_grids': {'ARBOR_GRID': [[{'text': 'School dinners, trips, uniform, swimming and after school clubs '
                                            'are paid for via Arbor. You can access the site using the link '
                                            'below.'},
                                   {'label': 'Go to Arbor',
                                    'href': 'http://malmesbury-church-of-england-primary-school.uk.arbor.sc',
                                    'color': 'blue',
                                    'external': True},
                                   {'label': 'Arbor App for Android',
                                    'href': 'https://play.google.com/store/apps/details?id=com.arboreducation.parentapp&amp;hl=en_GB',
                                    'color': 'cyan',
                                    'external': True},
                                   {'label': 'Arbor App for iPhone',
                                    'href': 'https://apps.apple.com/gb/app/arbor-parent-app/id1448707412',
                                    'color': 'cyan',
                                    'external': True}],
                                  [{'image': 'photos/Arbor.jpg',
                                    'alt': "Arbor app and portal: view your child's timetable, clubs and "
                                           'attendance, pay for school meals, update your details, receive '
                                           'messages, and sign up to trips and after-school clubs'}]]}},
 {'src': 'other/friends-of-malmesbury-primary-school.md',
  'out': 'friends-of-malmesbury/',
  'section': 'About',
  'title': 'Friends of Malmesbury Primary School (FOMPS)',
  'images': [{'src': 'montana-mark-cropped.jpg',
              'alt': 'Circus skills performer balancing on a unicycle while juggling',
              'caption': 'Circus skills day funded by the FOMPS'}]},
 {'src': 'other/newsletter.md',
  'out': 'newsletter/',
  'section': 'Community',
  'hidden': True,
  'downloads': [{'href': 'Malmesbury-and-Lyneham-Schools-in-Contact-Mag.pdf',
                 'label': 'Malmesbury and Lyneham Schools in Contact Magazine (PDF)'}]},
 {'src': 'other/school-tours.md', 'out': 'school-tours/', 'section': 'Information'},
 {'src': 'other/breakfast-club.md',
  'out': 'breakfast-club/',
  'section': 'Community',
  'title': 'Peas in the Pod'},
 {'src': 'other/clubs.md',
  'out': 'clubs/',
  'section': 'Community',
  'hidden': True,
  'images': [{'src': 'jamclub-pixelated.jpg', 'alt': 'Children decorating biscuits at JAM Club'}]}]
EXCLUDED = {'information/equality-information.md': '',
 'information/admissions-faqs.md': '',
 'other/my-calendar.md': '',
 'other/little-ducks.md': '',
 'about/results-footer-duplicate.md': '',
 'news/starting-school-this-september.md': '',
 'about/location.md': '',
 'learning/all-things-ipad.md': '',
 'news/archive-2024-2026.md': '',
 'news/archive-2020-2023.md': '',
 'news/archive-2018-2020.md': '',
 'news/archive-2015-2018.md': '',
 'information/document-library.md': ''}

def build():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copy(os.path.join(TEMPLATES, 'style.css'), _ensure_dir(os.path.join(DIST, 'css', 'style.css')))
    images_out = os.path.join(DIST, 'images')
    os.makedirs(images_out, exist_ok=True)
    if os.path.isdir(_os.path.join(BASE, 'admin')):
        shutil.copytree(_os.path.join(BASE, 'admin'), os.path.join(DIST, 'admin'))
    for name in ['montana-mark-cropped.jpg', 'school-439-pixelated.jpg', 'jamclub-pixelated.jpg', 'library-display.jpg']:
        shutil.copy(os.path.join(PROCESSED_IMAGES, name), os.path.join(images_out, name))
    shutil.copytree(os.path.join(PROCESSED_IMAGES, 'illustrations'), os.path.join(images_out, 'illustrations'), ignore=shutil.ignore_patterns('*.png'))
    photos_out = os.path.join(images_out, 'photos')
    os.makedirs(photos_out, exist_ok=True)
    if os.path.isdir(FETCHED_IMAGES):
        for name in os.listdir(FETCHED_IMAGES):
            shutil.copy(os.path.join(FETCHED_IMAGES, name), os.path.join(photos_out, name))
    icons_out = os.path.join(images_out, 'icons')
    os.makedirs(icons_out, exist_ok=True)
    if os.path.isdir(HOMEPAGE_ICONS):
        for name in os.listdir(HOMEPAGE_ICONS):
            if name in ('icon-duck.jpg', 'header-logo.png', 'footer-logo.png'):
                continue
            shutil.copy(os.path.join(HOMEPAGE_ICONS, name), os.path.join(icons_out, name))
    decor_out = os.path.join(images_out, 'decor')
    os.makedirs(decor_out, exist_ok=True)
    watermark_src = _os.path.join(BASE, 'assets/decor/crest-watermark.png')
    if os.path.isfile(watermark_src):
        shutil.copy(watermark_src, os.path.join(decor_out, 'crest-watermark.png'))
    documents_out = os.path.join(DIST, 'documents')
    os.makedirs(documents_out, exist_ok=True)
    if os.path.isdir(FETCHED_DOCS):
        for name in os.listdir(FETCHED_DOCS):
            shutil.copy(os.path.join(FETCHED_DOCS, name), os.path.join(documents_out, name))
    env.globals['hidden_pages'] = {pg['out'] for pg in PAGES if pg.get('hidden')}
    count = 0
    for page in PAGES:
        if page.get('hidden'):
            continue
        src_path = os.path.join(CONTENT, page['src'])
        with open(src_path, encoding='utf-8') as f:
            raw = f.read()
        fm_title = None
        m = re.search('^title:\\s*(.+)$', raw, re.MULTILINE)
        if m:
            fm_title = m.group(1).strip()
            if len(fm_title) > 1 and fm_title[0] == fm_title[-1] and fm_title[0] in '"\'':
                fm_title = fm_title[1:-1].replace("''", "'") if fm_title[0] == "'" else fm_title[1:-1].replace('\\"', '"')
        title = fm_title or page.get('title') or page['src']
        body_md = strip_body(raw, title=title)
        body_html = md_to_html(body_md)
        depth = page['out'].count('/')
        root = '../' * depth if depth else './'
        if '<!-- AUTHOR_BUTTONS -->' in body_html and page.get('author_links'):
            body_html = body_html.replace('<!-- AUTHOR_BUTTONS -->', author_buttons_html(page['author_links']))
        for marker, items in page.get('galleries', {}).items():
            placeholder = f'<!-- {marker} -->'
            if placeholder in body_html:
                body_html = body_html.replace(placeholder, gallery_html(root + 'images/', items))
        for marker, buttons in page.get('button_rows', {}).items():
            placeholder = f'<!-- {marker} -->'
            if placeholder in body_html:
                body_html = body_html.replace(placeholder, big_buttons_html(buttons))
        if page.get('governor_cards'):
            body_html = body_html.replace('<!-- GOVERNOR_CARDS -->', governor_cards_html(root + 'images/photos/', page['governor_cards']))
        for marker, rows in page.get('photo_rows', {}).items():
            body_html = body_html.replace(f'<!-- {marker} -->', photo_rows_html(root + 'images/photos/', rows))
        for marker, people in page.get('person_cards', {}).items():
            body_html = body_html.replace(f'<!-- {marker} -->', person_cards_html(root + 'images/', people))
        for marker, fig in page.get('portraits', {}).items():
            body_html = body_html.replace(f'<!-- {marker} -->', f'''<figure class="{fig.get('cls', 'portrait-figure')}"><img src="{root}images/{fig['src']}" alt="{fig['alt']}" loading="lazy"></figure>''')
        for marker, fig in page.get('inline_images', {}).items():
            placeholder = f'<!-- {marker} -->'
            if placeholder in body_html:
                body_html = body_html.replace(placeholder, inline_figure_html(root + 'images/', fig['src'], fig['alt'], fig.get('caption')))
        for marker, fig in page.get('figure_markers', {}).items():
            placeholder = f'<!-- {marker} -->'
            if placeholder in body_html:
                body_html = body_html.replace(placeholder, figure_html(root + 'images/', fig['src'], fig['alt'], fig.get('caption')))
        for marker, text in page.get('dividers', {}).items():
            placeholder = f'<!-- {marker} -->'
            if placeholder in body_html:
                body_html = body_html.replace(placeholder, divider_heading_html(text))
        for marker, tabs in page.get('tabs', {}).items():
            body_html = body_html.replace(f'<!-- {marker} -->', tabs_html(root + 'images/', marker.lower().replace('_', '-'), tabs))
        for marker, cols in page.get('button_grids', {}).items():
            placeholder = f'<!-- {marker} -->'
            body_html = body_html.replace(placeholder, button_grid_html(root + 'images/', cols))
        for marker, row in page.get('image_button_rows', {}).items():
            placeholder = f'<!-- {marker} -->'
            if placeholder in body_html:
                body_html = body_html.replace(placeholder, image_button_row_html(root + 'images/', row.get('image'), row['buttons'], image_first=row.get('image_first', True)))
        if page['src'] == 'home/index.md':
            full_content = render_homepage(root)
        else:
            extra_html = ''
            for img in page.get('images', []):
                extra_html += figure_html(root + 'images/', img['src'], img['alt'], img.get('caption'))
            extra_html += photo_grid_html(root + 'images/photos/', page.get('photos', []))
            extra_html += gallery_html(root + 'images/', page.get('gallery', []))
            extra_html += downloads_html(root, page.get('downloads', []))
            for img in page.get('images_after', []):
                extra_html += figure_html(root + 'images/', img['src'], img['alt'], img.get('caption'), css_class='wide-figure')
            if page.get('report_links'):
                extra_html += '<h2>Read the full reports</h2>' + report_links_html(root, page['report_links'])
            if page['src'] == 'information/document-library.md':
                extra_html += doc_library_html(_doc_library_categories())
            full_content = body_html + extra_html
        out_html = base_tpl.render(title=title, section=page.get('section'), content=full_content, root=root, noindex=PREVIEW_MODE, hero_image=page.get('hero_image'))
        out_dir = os.path.join(DIST, page['out'])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(out_html)
        count += 1
    not_found = base_tpl.render(title='Page not found', section=None, content="<p>Sorry, we couldn't find that page. Try the navigation above or head back to the <a href='./index.html'>homepage</a>.</p>", root='./', noindex=PREVIEW_MODE)
    with open(os.path.join(DIST, '404.html'), 'w', encoding='utf-8') as f:
        f.write(not_found)
    if PREVIEW_MODE:
        with open(os.path.join(DIST, 'robots.txt'), 'w', encoding='utf-8') as f:
            f.write('User-agent: *\nDisallow: /\n')
        print('PREVIEW_MODE is on: wrote robots.txt (Disallow: /) and added noindex meta tags. Set PREVIEW_MODE = False in build.py and rebuild once this is the real production site.')
    write_redirects()
    if not PREVIEW_MODE:
        urls = [SITE_URL + '/' + pg['out'] for pg in PAGES if not pg.get('hidden')]
        with open(os.path.join(DIST, 'sitemap.xml'), 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for u in urls:
                f.write(f'  <url><loc>{u}</loc></url>\n')
            f.write('</urlset>\n')
        with open(os.path.join(DIST, 'robots.txt'), 'w', encoding='utf-8') as f:
            f.write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n')
    print(f'Built {count} pages -> {DIST}')
    print(f'Excluded {len(EXCLUDED)} pages: {list(EXCLUDED.keys())}')
    hidden = [pg['src'] for pg in PAGES if pg.get('hidden')]
    if hidden:
        print(f'Hidden (kept in source, not published) {len(hidden)}: {hidden}')
SITE_URL = 'https://malmesburyprimaryschool.co.uk'
EXTRA_REDIRECTS = {'/online-learning-resources/': '/learning/curriculum/',
 '/parents/': '/parents/admissions/',
 '/british-values/': '/',
 '/homework/': '/',
 '/newsletter/': '/news/',
 '/clubs/': '/',
 '/results/': '/about/results/',
 '/location/': '/travel/',
 '/little-ducks/': '/',
 '/my-calendar/': '/information/term-dates/',
 '/equality-information/': '/information/policies-and-statements/',
 '/parents/admissions-faqs/': '/parents/admissions/',
 '/starting-school-this-september/': '/news/',
 '/all-things-ipad/': '/learning/e-safety/',
 '/tadpole-watch/': '/',
 '/6573-2/': '/',
 '/welcome-staff-page/': '/',
 '/welcome-governors-page-2-2/': '/',
 '/wp-login.php': '/',
 '/wp-admin/*': '/',
 '/documents/Music-Development-Plan-2025-26.pdf': '/documents/Music-Development-Plan-2026-27.pdf',
 '/documents/Morfa-Bay-June-2026-pixelated.pdf': '/documents/Morfa-Bay-June-2027-pixelated.pdf',
 '/documents/Morfa-Bay-June-2026-NEW.pdf': '/documents/Morfa-Bay-June-2027-pixelated.pdf',
 '/documents/Bank-MDSA-2025-26.zip': '/documents/Bank-MDSA-2026-27.zip',
 '/documents/2026-10-MDSA-temp.zip': '/information/current-vacancies/',
 '/documents/T2_MP2_Active-Planet.docx': '/documents/T2_MP2_Active-Planet.pdf'}

def write_redirects():
    shutil.copy(_os.path.join(BASE, 'generator/redirects.txt'), os.path.join(DIST, '_redirects'))

def _ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path
if __name__ == '__main__':
    build()

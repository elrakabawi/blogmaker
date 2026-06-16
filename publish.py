#!/usr/bin/python3
import datetime
import os
import shlex
import shutil
import subprocess
import sys
from html import escape


MATHJAX_SNIPPET = """
<script>
MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\(', '\\)']]
  }},
  svg: {{
    fontCache: 'global'
  }}
}};
</script>
<script type="text/javascript" id="MathJax-script" async
  src="{root_path}/scripts/tex-svg.js">
</script>
"""


TOGGLE_MARKUP = """
<div id="color-mode-switch">
  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75" aria-hidden="true">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
  </svg>
  <input type="checkbox" id="switch" />
  <label for="switch">Toggle color mode</label>
  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75" aria-hidden="true">
    <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
  </svg>
</div>
"""


COLOR_SCHEME_SCRIPT = """
<script type="text/javascript">
  const toggleDarkMode = () => {
    const root = document.documentElement;
    root.classList.toggle('dark');
  };

  const toggleColorScheme = () => {
    const colorScheme = localStorage.getItem('colorScheme');
    if (colorScheme === 'light') localStorage.setItem('colorScheme', 'dark');
    else localStorage.setItem('colorScheme', 'light');
  };

  const toggle = document.querySelector('#color-mode-switch input[type="checkbox"]');
  if (toggle) {
    toggle.onclick = () => {
      toggleDarkMode();
      toggleColorScheme();
    };
  }

  const checkColorScheme = () => {
    const colorScheme = localStorage.getItem('colorScheme');
    if (colorScheme === null || colorScheme === undefined) localStorage.setItem('colorScheme', 'light');
    if (colorScheme === 'dark' && toggle) {
      toggle.checked = true;
      toggleDarkMode();
    }
  };
  checkColorScheme();
</script>
"""


PAGE_FOOTER = """
</main>
</div>
</body>
</html>
"""


def extract_metadata(fil, filename=None):
    metadata = {}
    if filename:
        assert filename.endswith('.md')
        metadata['filename'] = filename[:-3] + '.html'
    while True:
        line = fil.readline()
        if line and line[0] == '[' and ']' in line:
            key = line[1:line.find(']')]
            value_start = line.find('(') + 1
            value_end = line.rfind(')')
            if key in ('category', 'categories'):
                metadata['categories'] = set(
                    x.strip().lower() for x in line[value_start:value_end].split(',')
                )
                metadata['categories'].discard('')
            else:
                metadata[key] = line[value_start:value_end]
        else:
            break
    return metadata


def defancify(text):
    return (
        text.replace("’", "'")
        .replace('“', '"')
        .replace('”', '"')
        .replace('…', '...')
        .replace('—', '--')
    )


def metadata_to_path(global_config, metadata):
    return os.path.join(
        global_config.get('posts_directory', 'posts'),
        metadata['date'],
        metadata['filename'],
    )


def get_printed_date(metadata):
    year, month, day = metadata['date'].split('/')
    month = 'JanFebMarAprMayJunJulAugSepOctNovDec'[int(month) * 3 - 3:][:3]
    return year + ' ' + month + ' ' + day


def get_primary_category(metadata):
    categories = sorted(metadata.get('categories', set()))
    return categories[0] if categories else ''


def get_url(global_config, route=''):
    domain = global_config['domain'].rstrip('/')
    route = route.strip('/')
    if not route:
        return domain
    return domain + '/' + route


def get_page_description(global_config, title, description=''):
    return description or global_config.get('description', title)


def make_head(root_path, page_title, description, global_config, canonical_route=''):
    full_title = page_title
    if page_title != global_config['title']:
        full_title = '{} | {}'.format(page_title, global_config['title'])

    head_bits = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        '<meta name="description" content="{}">'.format(escape(description)),
        '<title>{}</title>'.format(escape(full_title)),
        '<link rel="alternate" type="application/rss+xml" href="{}/feed.xml" title="{}">'.format(
            root_path, escape(global_config['title'])
        ),
        '<link rel="canonical" href="{}">'.format(escape(get_url(global_config, canonical_route))),
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;500;600&display=swap" rel="stylesheet">',
        '<link rel="stylesheet" type="text/css" href="{}/css/main.css">'.format(root_path),
        MATHJAX_SNIPPET.format(root_path=root_path),
        '<meta name="twitter:card" content="summary">',
        '<meta name="twitter:title" content="{}">'.format(escape(full_title)),
        '<meta name="twitter:image" content="{}">'.format(escape(global_config['icon'])),
        '</head>',
        '<body>',
    ]
    return '\n'.join(head_bits)


def make_site_header(root_path, global_config):
    nav_items = [
        '<a href="{}/index.html">Archive</a>'.format(root_path),
        '<a href="{}/feed.xml">RSS</a>'.format(root_path),
    ]
    if global_config.get('profile'):
        nav_items.append('<a href="{}" target="_blank" rel="noopener noreferrer">SNS</a>'.format(
            escape(global_config['profile'])
        ))

    description = ''
    if global_config.get('description'):
        description = '<p class="site-description">{}</p>'.format(
            escape(global_config['description'])
        )

    return """
<div class="site-shell">
  <header class="site-header">
    <div class="site-identity">
      <a class="site-brand" href="{root_path}/index.html">{site_title}</a>
      {description}
    </div>
    <div class="site-actions">
      <nav class="site-nav">
        {nav}
      </nav>
      {toggle}
    </div>
  </header>
  {color_script}
  <main id="doc" class="markdown-body comment-enabled" data-hard-breaks="true">
""".format(
        root_path=root_path,
        site_title=escape(global_config['title']),
        description=description,
        nav=''.join(nav_items),
        toggle=TOGGLE_MARKUP,
        color_script=COLOR_SCHEME_SCRIPT,
    )


def make_page_footer(root_path, global_config):
    footer_links = [
        '<a href="{}/feed.xml">RSS</a>'.format(root_path),
        '<a href="{}/index.html">Archive</a>'.format(root_path),
    ]
    if global_config.get('profile'):
        footer_links.append('<a href="{}" target="_blank" rel="noopener noreferrer">elrakabawi.sol</a>'.format(
            escape(global_config['profile'])
        ))

    return """
<footer class="site-footer">
  <div class="site-footer-line"></div>
  <div class="site-footer-links">{}</div>
</footer>
""".format(''.join(footer_links))


def make_categories_header(categories, root_path, active_category=None):
    links = [
        '<a class="category-link{}" href="{}/index.html">All</a>'.format(
            ' is-active' if active_category is None else '',
            root_path,
        )
    ]
    for category in categories:
        links.append(
            '<a class="category-link{}" href="{}/categories/{}.html">{}</a>'.format(
                ' is-active' if category == active_category else '',
                root_path,
                category,
                escape(category.capitalize()),
            )
        )
    return '<nav class="category-nav">{}</nav>'.format(''.join(links))


def make_toc_item(global_config, metadata, root_path):
    category = get_primary_category(metadata)
    category_html = ''
    if category:
        category_html = '<span class="post-category">{}</span>'.format(escape(category))

    link = metadata_to_path(global_config, metadata)
    return """
<li>
  <article class="post-preview">
    <div class="post-preview-meta">
      <span class="post-meta">{date}</span>
      {category}
    </div>
    <h2 class="post-preview-title">
      <a class="post-link" href="{link}">{title}</a>
    </h2>
  </article>
</li>
""".format(
        date=escape(get_printed_date(metadata)),
        category=category_html,
        link='{}/{}'.format(root_path, link),
        title=escape(metadata['title']),
    )


def make_toc(toc_items, global_config, all_categories, category=None):
    if category:
        title = category.capitalize()
        intro = 'Posts filed under {}.'.format(category)
        root_path = '..'
        canonical_route = 'categories/{}.html'.format(category)
        kicker = 'Category'
    else:
        title = global_config['title']
        intro = global_config.get('description', '')
        root_path = '.'
        canonical_route = ''
        kicker = 'Archive'

    body = """
<section class="page-header">
  <p class="page-kicker">{kicker}</p>
  <h1 class="page-title">{title}</h1>
  {intro}
</section>
{categories}
<ul class="post-list">
  {items}
</ul>
{footer}
""".format(
        kicker=escape(kicker),
        title=escape(title),
        intro='<p class="page-intro">{}</p>'.format(escape(intro)) if intro else '',
        categories=make_categories_header(all_categories, root_path, category),
        items=''.join(toc_items),
        footer=make_page_footer(root_path, global_config),
    )

    return (
        make_head(
            root_path,
            title,
            get_page_description(global_config, title, intro),
            global_config,
            canonical_route,
        )
        + make_site_header(root_path, global_config)
        + body
        + PAGE_FOOTER
    )


def make_post_page(global_config, metadata, html_body):
    root_path = '../../../..'
    route = metadata_to_path(global_config, metadata).replace(os.sep, '/')
    category = get_primary_category(metadata)
    kicker = category.capitalize() if category else 'Post'

    return (
        make_head(
            root_path,
            metadata['title'],
            get_page_description(global_config, metadata['title'], metadata.get('description', '')),
            global_config,
            route,
        )
        + make_site_header(root_path, global_config)
        + """
<article class="post">
  <header class="page-header">
    <p class="page-kicker">{kicker}</p>
    <h1 class="page-title">{title}</h1>
    <div class="page-meta">
      <span>{date}</span>
      <a href="{root_path}/index.html">All posts</a>
    </div>
  </header>
  <div class="article-body">
    {body}
  </div>
  {footer}
</article>
""".format(
            kicker=escape(kicker),
            title=escape(metadata['title']),
            date=escape(get_printed_date(metadata)),
            root_path=root_path,
            body=html_body,
            footer=make_page_footer(root_path, global_config),
        )
        + PAGE_FOOTER
    )


def generate_feed(global_config, metadatas):
    def get_date(date_text):
        year, month, day = (int(x) for x in date_text.split('/'))
        date = datetime.date(year, month, day)
        return date.strftime('%a, %d %b %Y 00:00:00 +0000')

    items = []
    for metadata in metadatas:
        items.append(
            """
<item>
  <title>{title}</title>
  <link>{link}</link>
  <guid>{link}</guid>
  <pubDate>{pub_date}</pubDate>
  <description>{description}</description>
</item>
""".strip().format(
                title=escape(metadata['title']),
                link=escape(get_url(global_config, metadata_to_path(global_config, metadata).replace(os.sep, '/'))),
                pub_date=get_date(metadata['date']),
                description=escape(metadata.get('description', '')),
            )
        )

    return """
<?xml version="1.0" ?>
<rss version="2.0">
<channel>
  <title>{title}</title>
  <link>{link}</link>
  <description>{description}</description>
  <image>
      <url>{icon}</url>
      <title>{title}</title>
      <link>{link}</link>
  </image>
{items}
</channel>
</rss>
""".strip().format(
        title=escape(global_config['title']),
        link=escape(get_url(global_config)),
        description=escape(global_config.get('description', global_config['title'])),
        icon=escape(global_config['icon']),
        items='\n'.join(items),
    )


def get_post_files():
    return sorted(
        os.path.join('posts', filename)
        for filename in os.listdir('posts')
        if filename.endswith('.md') and not filename.endswith('.swp')
    )


def run_pandoc(file_location, options):
    command = ['pandoc', '-o', '/tmp/temp_output.html', file_location]
    command.extend(shlex.split(options))
    subprocess.run(command, check=True)
    return defancify(open('/tmp/temp_output.html').read())


def sync_site(global_config):
    subprocess.run(
        ['rsync', '-av', 'site/.', '{}:{}'.format(global_config['server'], global_config['website_root'])],
        check=True,
    )


def copy_static_assets():
    os.makedirs('site', exist_ok=True)
    open(os.path.join('site', '.nojekyll'), 'w').write('')
    shutil.copytree('css', os.path.join('site', 'css'), dirs_exist_ok=True)
    shutil.copytree('scripts', os.path.join('site', 'scripts'), dirs_exist_ok=True)
    if os.path.isdir('images'):
        shutil.copytree('images', os.path.join('site', 'images'), dirs_exist_ok=True)


if __name__ == '__main__':
    global_config = extract_metadata(open('config.md'))

    if '--sync' in sys.argv:
        sync_site(global_config)
        sys.exit()

    file_locations = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    full_build = not file_locations
    if not file_locations:
        file_locations = get_post_files()
    if full_build and os.path.isdir('site'):
        shutil.rmtree('site')

    for file_location in file_locations:
        filename = os.path.split(file_location)[1]
        print('Processing file: {}'.format(filename))

        metadata = extract_metadata(open(file_location), filename)
        path = metadata_to_path(global_config, metadata)
        html_body = run_pandoc(file_location, metadata.get('pandoc', ''))
        total_file_contents = make_post_page(global_config, metadata, html_body)

        print('Path selected: {}'.format(path))

        truncated_path = os.path.split(path)[0]
        os.makedirs(os.path.join('site', truncated_path), exist_ok=True)

        out_location = os.path.join('site', path)
        open(out_location, 'w').write(total_file_contents)

    metadatas = []
    categories = set()
    for filename in os.listdir('posts'):
        if filename.endswith('.md') and not filename.endswith('.swp'):
            metadata = extract_metadata(open(os.path.join('posts', filename)), filename)
            metadatas.append(metadata)
            categories = categories.union(metadata.get('categories', set()))
    categories = sorted(categories)

    print('Detected categories: {}'.format(' '.join(categories)))

    sorted_metadatas = sorted(metadatas, key=lambda x: x['date'], reverse=True)
    feed = generate_feed(global_config, sorted_metadatas)

    os.makedirs(os.path.join('site', 'categories'), exist_ok=True)

    print('Building tables of contents...')

    homepage_toc_items = [
        make_toc_item(global_config, metadata, '.')
        for metadata in sorted_metadatas
        if global_config.get('homepage_category', '') in metadata['categories'].union({''})
    ]

    for category in categories:
        category_toc_items = [
            make_toc_item(global_config, metadata, '..')
            for metadata in sorted_metadatas
            if category in metadata['categories']
        ]
        toc = make_toc(category_toc_items, global_config, categories, category)
        open(os.path.join('site', 'categories', category + '.html'), 'w').write(toc)

    open('site/feed.xml', 'w').write(feed)
    open('site/index.html', 'w').write(make_toc(homepage_toc_items, global_config, categories))

    copy_static_assets()

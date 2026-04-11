import os
from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.tags = []
        self.void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.tags.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag not in self.void_elements:
            if not self.tags:
                print(f"{self.filename}: Error - found end tag </{tag}> but no start tags open at {self.getpos()}")
            else:
                last_tag, pos = self.tags.pop()
                if last_tag != tag:
                    print(f"{self.filename}: Error - Mismatched tag: expected </{last_tag}> but found </{tag}> at {self.getpos()} (start tag was at {pos})")
                    # Try to recover by popping until match
                    while self.tags:
                        t, p = self.tags.pop()
                        if t == tag:
                            break

for root, dirs, files in os.walk('app/templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # strip jinja blocks conservatively to avoid html parse errors
                import re
                content = re.sub(r'\{%.*?%\}', '', content)
                content = re.sub(r'\{\{.*?\}\}', '', content)
                parser = MyHTMLParser(file)
                try:
                    parser.feed(content)
                    if parser.tags:
                        print(f"{file}: Unclosed tags left: {[t[0] for t in parser.tags]}")
                except Exception as e:
                    print(f"{file}: Parsing error {e}")

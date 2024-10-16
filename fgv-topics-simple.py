import sys
import re

def get_breakdown(text:str, topic:str, prefix:str=''):
    match = re.findall('[:,;]\s*([^:,;]+)', text) if ':' in text else None

    if not match:
        return text

    if ' e ' in match[-1]:
        line = match.pop(-1)
        match += line.split(' e ')

    output = \
        text.split(':')[0] + ':\n'\
        + '\n'.join(f'{prefix}{topic}.{i}. {m}' for i, m in enumerate(match, 1))

    return output

def int2roman(num:int):
    if num == 0:
        return '0'

    roman_numerals = [
        ('M', 1000),
        ('CM', 900),
        ('D', 500),
        ('CD', 400),
        ('C', 100),
        ('XC', 90),
        ('L', 50),
        ('XL', 40),
        ('X', 10),
        ('IX', 9),
        ('V', 5),
        ('IV', 4),
        ('I', 1),
    ]

    roman_string = '' if num > 0 else '-'

    for symbol, value in roman_numerals:
        count = num // value
        roman_string += symbol * count
        num -= value * count

    return roman_string

filein = sys.argv[1]
fileout = re.sub('\.(\w+)$', '', filein) + '.out'

patterns = {
    'title': '^•.*$'
    'subtitle': '^\s*([\sA-Z0-9ÇÁÀÃÂÄÉÊÍÏÓÕÔÖÚÜ]+):?.*$',
    'topic': '[\.:]\s*(\d+(?:\.\d+)*)\.\s*([^\.]+)',
}

output = ''

with open(sys.argv[1]) as handle:
    input = handle.readlines()

counter = 0

for line in input:
    if line.strip():
        line = re.sub(
            'art\.',
            'art',
            re.sub(
                '(\d+)\.(\d{3})',
                '\\1\\2',
                line,
            ),
        )

        counter += 1
        title = re.match(patterns['title'], line).groups()[0].strip()
        output += f'{int2roman(counter)}. {title}'
        print(title)

        for topic, content in re.findall(patterns['topic'], line):
            print(topic,content)
            tabs = len(topic.split('.'))
            #content = get_breakdown(content, topic, (tabs + 1) * chr(9))
            output += f'\n{tabs * chr(9)}{topic}. {content}'
        output += '\n\n'
 
with open(fileout, 'w') as handle:
    handle.write(output)
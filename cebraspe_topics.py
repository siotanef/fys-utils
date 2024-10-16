# python cebraspe_topics.py <filename>.txt

import os
import sys
import re

from typing import Iterable

def int2roman(num:int):
    if num == 0:
        return '0'

    roman_min = 0
    roman_max = 9999

    if num < roman_min or num > roman_max:
        raise ValueError(f'Number {num:,} out of range [{roman_min:,},{roman_max:,}].')
    
    roman_digits = {
        1000: 'M', 
        900: 'CM', 
        500: 'D', 
        400: 'CD',
        100: 'C', 
        90: 'XC', 
        50: 'L', 
        40: 'XL',
        10: 'X', 
        9: 'IX', 
        5: 'V', 
        4: 'IV', 
        1: 'I',
    }

    roman = ''

    for key, val in roman_digits.items():
        while num >= key:
            num -= key
            roman += val
        
    return roman

def get_topic_pattern(it:Iterable[int], sep:str=r'\.',):
    return sep.join(str(i) for i in it)

def get_next_topics(current:str=None, sep:str=r'\.',):
    if not current:
        return {1: get_topic_pattern([1,])} 
    
    current = [int(i) for i in current.split(sep)]

    return dict(reversed([
        (
            i + 1,
            get_topic_pattern(
                current + [1,]
                if i == len(current) else
                current[:i] + [current[i] + 1],
                sep=sep,
            ),
        ) for i in range(len(current) + 1)
    ]))

def get_breakdown(
    text:str,
    sep:str=r'\.',
    prefix:str=r'\s',
    suffix:str=r'\.?\s',
    threshold:int=3,
):
    output = ''
    current = None
    previous_level = None
    index = 0
    strikes = 0
    
    while index < len(text):
        next = None
        next_topic = None

        for level, topic in get_next_topics(current, sep,).items():
            next_topic = topic
            pattern = f'^.*({prefix}{topic}{suffix})'
            match = re.match(pattern, text[index:])

            if match:
                start = match.start(1)
                
                if next is None or start < next:
                    next = start
                    current = topic
                    l = level

        if next is None:
            if strikes < threshold:
                current = next_topic
                strikes += 1
                continue
            
            next = len(text)                
        else:
            strikes = 0
            next += index

        if previous_level:
            output += (previous_level * '\t') + text[index:next].strip() + '\n'
        
        index = next
        previous_level = l

    return output
    

def main():
    assert\
        len(sys.argv) >= 2\
        and sys.argv[1].endswith('.txt')\
        and os.path.isfile(sys.argv[1]),\
        'Invalid "*.txt" file path.'
    
    filepath = sys.argv[1]
    text = ''

    with open(filepath) as handle:
        text = re.sub(
            '[\\n\\t\\s]+',
            ' ',
            handle.read(),
        )
    
    char_upper = 'A-Z,\u00C0-\u00D6\u00D8-\u00DE'
    char_lower = 'a-z,\u00E0-\u00F6\u00F8-\u00FF'
    char_numbers = '\\d'
    char_symbols = '\\_\\-'
    char_space = '\\s'

    topics = []
    char_topic_start = char_upper + char_numbers + char_symbols
    char_topic = char_topic_start + char_space

    pattern_main = f'([{char_topic_start}][{char_topic}]+)\\:\\s*1[\\.\\s]'
    matches = re.finditer(pattern_main, text)


    if matches is None:
        raise ValueError('No topic matches for "{filepath}".')

    indexes = [(match.start(1), match.end(1)) for match in matches] + [(len(text), None,),]
    topics = {
        text[slice(*i)]: get_breakdown(' ' + text[i[-1] + 1: indexes[index + 1][0]].strip())
        for index, i in enumerate(indexes[:-1])
    }


    text = '\n'.join(f'{int2roman(index)}. {key}\n{val}' for index, (key,val,) in enumerate(topics.items(), 1))
    #print(text)
    print(indexes)
    #print(topics[list(topics.keys())[0]])


    with open(re.sub('(\\.txt)$', '.out', filepath), 'w') as handle:
        handle.write(text)


if __name__ == '__main__':
    sys.exit(main())
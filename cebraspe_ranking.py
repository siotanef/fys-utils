import io
import re
import sys
import pandas as pd

from typing import Iterable
from PyPDF2 import PdfReader

def cast(s:str):
  if re.match(r'^\d+$', s):
    return int(s) 

  if re.match(r'^\d+[.]\d+$', s):
    return float(s)

  return s

# with io.open('res.txt', encoding='utf-8') as handle:
#   lines = ' '.join(line.strip().replace('\n', '').replace('|', ' ') for line in handle.readlines())

# #lines = ' '.join(page.extract_text().replace('\n', ' ') for page in PdfReader('res.pdf').pages)

# columns = [column.strip() for column in re.findall('na seguinte ordem: ([^\.]+).', lines)[0].split(',')]
# last = columns.pop(-1)
# columns += last.split(' e ')

# groups = [
#   [cast(cell.strip()) for cell in row[0].split(',')]
#   for row in re.findall('(\d{8}\s*,[\sA-Za-z]+(,\s?[\d\.]+[\d]\s*){6})', lines)
# ]

# df = pd.DataFrame(groups, columns=columns)
# df['final'] = df[df.columns[-2]] + df[df.columns[-1]]
# df = df.sort_values('final', ascending=False, ignore_index=True,)
# pd.set_option("display.max_colwidth", None)
# print(df)

def join_lines(
    it:Iterable[str],
):
   return ' '.join(i.strip() for i in it)

def get_pdf_lines(
    pdf:str,
):
    return list(map(
       lambda s: s.strip(),
       filter(
        lambda l: re.match('^\d{,6}\s*$', l) is None,
        '\n'.join(page.extract_text() for page in PdfReader(pdf).pages).split('\n'),
        ),
    ))

def get_pdf_topics(
    lines:Iterable[str],
    pattern:str='([\s\d]{8,})\s*,([^/,]+),([\s\.\,\d]+)',
):
    topics = {}
    flag = False
    current_index = None

    groups = {
        'id': lambda s: int(re.sub('\D', '', s)),
        'name': lambda s: s.replace(' ', ''),
        'grades': lambda s: [float(re.sub('\.$', '', re.sub('[^\d\.]', '', i.strip()))) for i in s.split(',')],
    }

    for index, line in enumerate(lines):
       m = re.match('^(\d+(?:\.\d+)*)\s(.*)$', line)
       n = re.match('^.*' + pattern, line)

       if not n:
          if m:
            flag = True
            
            if current_index and len(topics[current_index]) == 1:
                topics[current_index].append(index - 1)

            current_index = index
            topics[current_index] = []
            continue
          if current_index is not None and not flag and len(topics[current_index]) == 1:
            topics[current_index].append(index)
          continue
       
       if flag:
          flag = False
          topics[current_index].append(index)
       
       
    return {
       join_lines(lines[key:val[0]]): get_candidates(
          join_lines(lines[val[0]:val[1] + 1]),
          pattern=pattern,
          groups=groups,
        )
       for key,val in topics.items()
       if len(val) == 2
    } 
   
def get_candidates(
    text:str,
    pattern:str='([\s\d]{8,})\s*,([^/,]+),([\s\.\,\d]+)',
    groups:list=None,
):
    matches = re.finditer(pattern, text)
    output = []

    for m in matches:      
        output.append([function(m.group(index)) for index, function in enumerate(groups.values(), 1)])

    return pd.DataFrame(
       data=output,
       columns=groups.keys(),
    )

def optional_spaces(pattern:str):
   return '\s?'.join(pattern)

def join_dataframes(
    topics:dict,
):
    data = []
    cargo = None
    vaga = None
    criterios = None
    pattern_cargo = f'^.*({optional_spaces("área")}|{optional_spaces("cargo")})'
    pattern_vaga = f'^.*({optional_spaces("negro")}|{optional_spaces("deficiência")})'
    pattern_criterios = f'^.*na seguinte ordem:(.+)\.\s*$'


    for key,val in topics.items():
        o = re.match(pattern_criterios, key, re.IGNORECASE)

        if o:
            criterios = [s.strip() for s in o.group(1).split(',')]

            if ' e ' in criterios[-1]:
               c = criterios.pop(-1).split(' e ')

               criterios.append(' e '.join(c[:-1]))
               criterios.append(c[-1])

            criterios = criterios[len(val.columns) - 1: ]
            criterios = [s.replace(' ', '') for s in criterios]
            break
        
    for key,val in topics.items():
        m = re.match(pattern_cargo, key, re.IGNORECASE)
        cargo = ':'.join(key.split(':')[1:]).strip().lower() if m else cargo

        n = re.match(pattern_vaga, key, re.IGNORECASE)
        vaga = ('pcd' if n.group(1) == 'deficiência' else 'negro') if n else 'ampla'

        val.insert(0, 'vaga', vaga)
        val.insert(0, 'cargo', re.sub('\s?,\s?', ',', cargo.replace('–', ',').replace(' ','')))
        grades = pd.DataFrame(val[val.columns[-1]].tolist(), columns=criterios)
        
        val = pd.concat(
            [
                val[val.columns[:-1]],
                grades,
            ],
            axis=1,
        )
        
        data.append(val)

    df = pd.concat(data)

    return df

def get_dataframe(pdf:str):   
    lines = get_pdf_lines(pdf)
    topics = get_pdf_topics(lines)

    with open(re.sub(f'(\.{pdf.split(".")[-1]})$', '.out', pdf), 'w') as handle:
        handle.writelines(map(lambda s: f'{s}\n', lines,))

    return join_dataframes(topics)

def main():
    dfs = [get_dataframe(pdf) for pdf in sys.argv[1:]]
    assert all(df[df.duplicated(subset=['cargo','vaga','id'], keep=False)]['id'].unique().size == 0 for df in dfs)
    df = pd.merge(
       *[df.drop(['name', 'cargo'], axis=1) if index else df for index,df in enumerate(dfs)],
       on=['id', 'vaga'],
       how='inner',
    )
    grades = list(df.columns[-4:-2]) + list(df.columns[-1:])
    df.insert(len(df.columns), 'total', df[grades].sum(axis=1).round(2))
    sorting = list(df.columns[:2]) + list(df.columns[-1:])
    df = df.sort_values(sorting, ascending=[True, True, False]).reset_index(drop=True)
    df.insert(3, 'posicao', df.groupby(list(df.columns[:2])).cumcount() + 1)
    df = df.reset_index(drop=True)
    df.to_csv('merge.csv')

if __name__ == '__main__':
    sys.exit(main())
# with open('res.txt') as handle:
#   lines = ' '.join(line.strip().replace('\n', '') for line in handle.readlines()).split('/')
# lines = [sum([float(i[:-1]) for i in line.split(',')[-2:]]) for line in lines]
# for line in enumerate(sorted(lines, key=lambda x: -x), 1):
#   print(line)
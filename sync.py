"""Export only approved machine fields from Tencent Docs to public/data.json.

Required GitHub Actions secrets: TENCENT_ACCESS_TOKEN, TENCENT_CLIENT_ID,
TENCENT_OPEN_ID. OAuth token lifecycle must be managed by the owner.
"""
import json
import os
import pathlib
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

FILE_ID = 'DWWxsb0ROcmtaUW5t'
SHEET_ID = os.getenv('TENCENT_SHEET_ID', '000002')
RANGE = os.getenv('TENCENT_RANGE', 'A1:AZ5000')
# CHANGE THESE to exactly match the row-1 column headers in Tencent Docs.
HEADERS = {
    'model': os.getenv('COL_MODEL') or 'model',
    'serial': os.getenv('COL_SERIAL') or 'serial numbers',
    'yom': os.getenv('COL_YOM') or 'YOM',
    'status': os.getenv('COL_STATUS') or 'STOCK IN WEERT',
    'eta': os.getenv('COL_ETA') or 'eta IN wEERT wAREHOUSE',
}
ALLOWED = {'IN PRODUCTION', 'IN TRANSIT', 'YES - IN WEERT'}


def read_rows():
    url = ('https://docs.qq.com/openapi/spreadsheet/v2/files/' +
           quote(FILE_ID, safe='') + '/sheets/' + quote(SHEET_ID, safe='') +
           '/values?range=' + quote(RANGE, safe=''))
    request = Request(url, headers={
        'Access-Token': os.environ['TENCENT_ACCESS_TOKEN'],
        'Client-Id': os.environ['TENCENT_CLIENT_ID'],
        'Open-Id': os.environ['TENCENT_OPEN_ID'],
    })
    with urlopen(request, timeout=25) as response:
        payload = json.load(response)
    if payload.get('ret') != 0:
        raise RuntimeError('Tencent API returned an error: ' + str(payload.get('msg', payload.get('ret'))))
    values = payload.get('data', {}).get('values')
    if not isinstance(values, list) or not values:
        raise ValueError('No sheet values returned; check API access, sheet ID, and range')
    return values


def cell_to_text(value):
    if value is None:
        return ''
    if isinstance(value, dict):
        # Some API representations return cell objects rather than bare strings.
        for key in ('formattedValue', 'displayValue', 'value', 'text'):
            if key in value:
                return cell_to_text(value[key])
        raise ValueError('Unexpected Tencent cell object; inspect API schema privately')
    return str(value).strip()


def build(rows=None):
    if rows is None:
        rows = read_rows()
    header = [' '.join(cell_to_text(x).casefold().split()) for x in rows[0]]
    missing = [name for name in HEADERS.values() if ' '.join(name.casefold().split()) not in header]
    if missing:
        raise ValueError('Missing configured column headers: ' + ', '.join(missing))
    ix = {field: header.index(' '.join(name.casefold().split())) for field, name in HEADERS.items()}
    machines = []
    for row in rows[1:]:
        def value(field):
            i = ix[field]
            return cell_to_text(row[i]) if i < len(row) else ''
        status = ' '.join(value('status').upper().split())
        if status not in ALLOWED:
            continue
        model, serial = value('model'), value('serial')
        if not model and not serial:
            continue
        machines.append({'model': model, 'serial': serial, 'yom': value('yom'), 'eta': value('eta'), 'status': status})
    destination = pathlib.Path('docs/data.json')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        'updatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'machines': machines,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Successfully exported {len(machines)} approved machine rows.')


if __name__ == '__main__':
    build()

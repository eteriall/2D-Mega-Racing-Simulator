import json

d = json.load(open('tasks.json'))
json.dump(d, open('tasks.json', mode='w', encoding='utf-8'), ensure_ascii=False)
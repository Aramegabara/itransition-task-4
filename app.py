import os, json, yaml, pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, send_from_directory, request, jsonify
from task_4 import analyze_store, STORES

load_dotenv()
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

LAST_TABLE = {}

TOOLS = [{
    'type': 'function',
    'function': {
        'name': 'filter_users',
        'description': 'Show users of a store whose column matches a regex. '
                       'Columns: id, name, address, phone, email.',
        'parameters': {
            'type': 'object',
            'properties': {
                'store': {'type': 'string', 'enum': list(STORES)},
                'column': {'type': 'string', 'enum': ['id', 'name', 'address', 'phone', 'email']},
                'pattern': {'type': 'string', 'description': 'Python regex, e.g. ^[sp] for starts with s or p'},
            },
            'required': ['store', 'column', 'pattern'],
        },
    },
},
{
    'type': 'function',
    'function': {
        'name': 'filter_books',
        'description': 'Show books of a store whose column matches a regex. Columns: title, author.',
        'parameters': {
            'type': 'object',
            'properties': {
                'store': {'type': 'string', 'enum': list(STORES)},
                'column': {'type': 'string', 'enum': ['title', 'author']},
                'pattern': {'type': 'string', 'description': 'Python regex'},
            },
            'required': ['store', 'column', 'pattern'],
        },
    },
},
{
  'type': 'function',
  'function': {
    'name': 'get_store_summary',
    'description': 'Precomputed stats for one store: top 5 revenue days, unique users, '
                   'unique author sets, most popular authors, best buyer.',
    'parameters': {
      'type': 'object',
      'properties': {'store': {'type': 'string', 'enum': STORES}},
      'required': ['store'],
    },
  },
}]
RESULTS = {store: analyze_store(store) for store in STORES}

app = Flask(__name__, static_folder='.', static_url_path='')


@app.route('/')
def index():
  return send_from_directory('.', 'index.html')

@app.route('/ask', methods=['POST'])
def ask_route():
    LAST_TABLE.clear()
    answer = ask(request.json['question'])
    return jsonify({'answer': answer, 'table': LAST_TABLE.get('html', '')})

def get_store_summary(store: str) -> dict:
  r = RESULTS[store]
  return {
    'top_five_days': str(r['top_five']),
    'unique_users': int(r['unique_users']),
    'author_sets': int(r['author_sets']),
    'top_authors': str(r['top_authors']),
    'best_buyer_ids': str(r['best_buyer']),
    'best_buyer_name': str(r['best_name']),
  }

def filter_users(store:str, column: str, pattern: str) -> str:
  df = pd.read_csv(f'{store}/users.csv')
  mask = df[column].astype(str).str.contains(pattern, case=False, regex=True, na=False)
  result = df[mask]
  LAST_TABLE['html'] = result.to_html(index=False)
  return f'{len(result)} users found'

def filter_books(store: str, column: str, pattern: str) -> str:
    with open(f'{store}/books.yaml', encoding='utf-8') as f:
        df = pd.DataFrame(yaml.safe_load(f))
    df.columns = [c.lstrip(':') for c in df.columns]
    mask = df[column].astype(str).str.contains(pattern, case=False, regex=True, na=False)
    result = df[mask]
    LAST_TABLE['html'] = result.to_html(index=False)
    return f'{len(result)} books found'


FUNCTIONS = {
    'get_store_summary': get_store_summary,
    'filter_users': filter_users,
    'filter_books': filter_books,
}

def ask(question: str) -> str:
  messages = [
    {'role': 'system', 'content': 'You answer questions about bookstore data. '
     'Always use the tools to get numbers, never guess. Answer brifly.'},
    {'role': 'user', 'content': question},
  ]
  while True:
    response = openai_client.chat.completions.create(
      model='gpt-4o-mini', messages=messages, tools=TOOLS)
    msg = response.choices[0].message
    if not msg.tool_calls:
      return msg.content
    messages.append(msg)
    for call in msg.tool_calls:
      args = json.loads(call.function.arguments)
      result = FUNCTIONS[call.function.name](**args)
      messages.append({'role': 'tool', 'tool_call_id': call.id,
                       'content': json.dumps(result)})


if __name__ == '__main__':
  app.run(debug=True, port=5000)
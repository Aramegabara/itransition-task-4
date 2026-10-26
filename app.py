import os, json
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, send_from_directory, request, jsonify
from task_4 import analyze_store, STORES

load_dotenv()
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

TOOLS = [{
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
  question = request.json['question']
  return jsonify({'answer': ask(question)})

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
      result = get_store_summary(**args)
      messages.append({'role': 'tool', 'tool_call_id': call.id,
                       'content': json.dumps(result)})


if __name__ == '__main__':
  app.run(debug=True, port=5000)
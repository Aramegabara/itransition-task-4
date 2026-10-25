import yaml, re, pandas as pd
from itertools import combinations


STORES = ['STORE1', 'STORE2', 'STORE3', 'STORE4', 'STORE5']
EURO_TO_USD = 1.2

def parse_price(raw):
  if pd.isna(raw):
    return None

  s = str(raw).strip()
  is_eur = ('€' in s) or ('EUR' in s.upper())

  if '¢' in s:
    nums = re.findall(r'\d+', s)
    value = int(nums[0]) + int(nums[1]) / 100
  else:
    m = re.search(r'\d+(?:\.\d+)?', s)
    value = float(m.group())

  if is_eur:
    value = value * EURO_TO_USD
  return round(value, 2)

def to_author_set(authors):
  return tuple(sorted(author.strip() for author in authors.split(',')))

def reconcile_users(users):
  parent = {i:  i for i in users['id']}

  def find_person(usr_id):
    while parent[usr_id] != usr_id:
      usr_id = parent[usr_id]
    return usr_id

  def union(first, second):
    first_person, second_person = find_person(first), find_person(second)
    if first_person != second_person:
      parent[max(first_person, second_person)] = min(first_person, second_person)

  key_names = ['name', 'address', 'phone', 'email']
  for keys in combinations(key_names, 3):
    for _, group in users.groupby(list(keys))['id']:
      ids = list(group)
      for id in ids[1:]:
        union(ids[0], id)

  return users['id'].map(find_person)

def analyze_store(store):
  users = pd.read_csv(f'{store}/users.csv')
  orders = pd.read_parquet(f'{store}/orders.parquet')
  with open(f'{store}/books.yaml', encoding='utf-8') as f:
    books = pd.DataFrame(yaml.safe_load(f))
    
  orders['price_usd'] = orders['unit_price'].map(parse_price)
  orders['dt'] = pd.to_datetime(
    orders['timestamp'].str.replace(r'[,;]', ' ',regex=True)
    .str.replace(r'(?i)\b([ap])\.m\.?', r'\1m', regex=True)
    .str.replace(r'\s+', ' ', regex=True)
    .str.strip(),
    format='mixed', errors='coerce')
  orders['paid_price'] = orders['quantity'] * orders['price_usd']

  orders['date'] = orders['dt'].dt.date
  orders['year'] = orders['dt'].dt.year
  orders['month'] = orders['dt'].dt.month
  orders['day'] = orders['dt'].dt.day

  daily = orders.groupby('date')['paid_price'].sum()
  top_five = daily.sort_values(ascending=False).head(5)

  users['person'] = reconcile_users(users)
  unique_users = users['person'].nunique()

  books['author_set'] = books[':author'].map(to_author_set)
  author_sets = books['author_set'].nunique()

  orders_books = orders.merge(
    books[[':id', 'author_set']],
    left_on='book_id',
    right_on=':id'
  )

  sold = orders_books.groupby('author_set')['quantity'].sum()
  top_authors = sold.sort_values(ascending=False)

  orders_person = orders.merge(
    users[['id', 'person']],
    left_on='user_id',
    right_on='id'
  )

  spending = orders_person.groupby('person')['paid_price'].sum()
  best_person = spending.idxmax()

  best_buyer = sorted(users.loc[users['person'] == best_person, 'id'])
  best_name = users.loc[users['person'] == best_person, 'name'].iloc[0]

  return {
    'store': store,
    'top_five': top_five,
    'unique_users': unique_users,
    'author_sets': author_sets,
    'top_authors': top_authors,
    'best_buyer': best_buyer,
    'best_name': best_name,
    'daily': daily,
  }

if __name__ == '__main__':
  for store in STORES:
      result = analyze_store(store)
      print(f'=== {result['store']} ===')
      print(f'Top 5 days by revenue: \n{result['top_five'].rename_axis(None).to_string()}')
      print(f'Unique users: {result['unique_users']}')
      print(f'Unique author sets: {result['author_sets']}')
      print(f'Most popular authors: {", ".join(result['top_authors'].index[0])}')
      print(f'Best buyer: {result['best_buyer']}')

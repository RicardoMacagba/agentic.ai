import google.genai as g
from inspect import signature
print('Client sig', signature(g.Client))
client = g.Client()
print('Has chats', hasattr(client, 'chats'))
print('Has models', hasattr(client, 'models'))
print('Chats members', [x for x in dir(client.chats) if 'create' in x.lower() or 'send' in x.lower()][:50])
print('Models members', [x for x in dir(client.models) if 'embed' in x.lower() or 'generate' in x.lower()][:50])

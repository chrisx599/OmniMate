from openai import OpenAI

client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="token-abc123",
    )

# list models
models = client.models.list()
for model in models.data:
    print(model.id)

completion = client.chat.completions.create(
  model="Qwen2.5-14B-Instruct-1M",
  messages=[
    {"role": "user", "content": "Hello!"}
  ]
)

print(completion.choices[0].message.content)

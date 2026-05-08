from app.extension import client

def ai_chat(prompt):

    response = client.chat.completions.create(
        model="baidu/cobuddy:free",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        extra_body={
            "reasoning": {
                "enabled": True
            }
        }
    )

    return response.choices[0].message.content
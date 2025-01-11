import streamlit as st
from elevenlabs import play
import requests
from openai import OpenAI
import base64

def get_response(client, question):
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id='asst_n2Hh1HVxRl9vFE7fJarIOvEQ',
        instructions="*** if user submits a address not in database, return 'NA' only 2 letters ***,Answer the question only if its relevant to real estate, do not include astericks, full stop etc, structure the response for Text to speech,*** if user submits something you can not answer, return 'NA' only 2 letters ***"
    )

    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        output = ''
        for message in messages.data:
            for block in message.content:
                if block.type == 'text':
                    output += block.text.value + '\n'
        output = output.replace(question, '')
        if 'not found' in output.lower():
            output = 'NA'
        return output
    else:
        return 'Error'

def get_perplexity_response(qs):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise, give output in listed manner, text to speech friendly"
            },
            {
                "role": "user",
                "content": qs
            }
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 50,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }
    headers = {
        "Authorization": f"Bearer {st.secrets['PERPLEXITY_API_KEY']['PERPLEXITY_API_KEY']}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    js = response.json()['choices'][0]['message']['content']
    return js

def main():
    
    client = OpenAI(api_key=st.secrets['OPENAI_API_KEY']['OPENAI_API_KEY'])

    st.title("NYC Real Estate LLM")

    user_input = st.text_input("Your Question:")

    if st.button("Ask") and user_input:
        st.empty()
        st.write('Looking for relevant data in records')
        answer = get_response(client, user_input).strip()
        if answer == 'NA':
            st.write('Thinking...')
            answer = get_perplexity_response(user_input)

        st.write(answer)

        elevenlabs_api_key = st.secrets['ELEVENLABS_API_KEY']['ELEVENLABS_API_KEY']
        url = "https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": elevenlabs_api_key,
        }
        symbols = [',', '.', '*', ';', ':', '[', ']', '+', '-', '^', '(', ')', '?', '|', '+', '_']
        for q in symbols:
            answer = answer.replace(q, '')
        data = {
            "text": answer,
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75,
            },
        }

        tts_response = requests.post(url, headers=headers, json=data)

        if tts_response.status_code == 200:

            audio_bytes = tts_response.content
            b64_audio = base64.b64encode(audio_bytes).decode()

            audio_html = f"""
                <audio autoplay controls>
                    <source src="data:audio/mpeg;base64,{b64_audio}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
        else:
            st.error(f"Error: {tts_response.status_code}, {tts_response.text}")

main()

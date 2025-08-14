import os
import json

from openai import OpenAI

from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_city_description(day_weather: str, geo_data: str) -> Dict[str, str]:
    
    prompt = """
    Ты - эксперт по погоде.
    Ты получаешь данные о погоде и данные о городе.
    Ты должен сгенерировать описание погоды для данного дня.
    Ты должен также сгенерировать, что одеться для данного дня, учитывая текущую погоду и то, как она будет меняться в течение дня.
    Верни описание в формате JSON с полями:
    {
        "description": "описание погоды для данного дня",
        "what_to_wear": "что одеться для данного дня, учитывая текущую погоду и то, как она будет меняться в течение дня"
    """
    
    
    # prompt = """
    # You are a weather expert.
    # You are given a day's weather data and a geo data of a city.
    # You need to generate a description of the day's weather.
    # You need also to generate what to wear for the day considering current weather and how it is going to change during the day.
    # Return the description in JSON format with the following fields:
    # {
    #     "description": "description of the day's weather",
    #     "what_to_wear": "what to wear for the day considering current weather and how it is going to change during the day"
    # }
    # """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages = [
                {"role": "system", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        content = response.choices[0].message.content
        description_data = json.loads(content)

        required_fields = ["description", "what_to_wear"]
        for field in required_fields:
            if field not in description_data:
                raise ValueError(f"Missing required field: {field}")

        return description_data
    except Exception as e:
        print(f"Error generating city description: {e}")
        return {"description": "", "what_to_wear": ""}
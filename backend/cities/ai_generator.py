import os
import json

from openai import OpenAI

from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def tream_data(day_weather: dict, geo_data: dict):
    addr= geo_data['addresses'][0]['address']
    city = addr['municipality']
    country = addr['country']
    cur = day_weather['current']
    daily = day_weather['daily'][0]

    def wdesc(wx):
        return wx.get('weather', [{}])[0].get('description')

    
    data = {
        "geo": {"city": city, "country": country},
        "weather": {
            "timezone": day_weather.get('timezone'),
            "timezone_offset": day_weather.get('timezone_offset'),
            "current": {
                "dt": cur.get('dt'),
                "temp": cur.get('temp'),
                "humidity": cur.get('humidity'),
                "uvi": cur.get('uvi'),
                "wind_speed": cur.get('wind_speed'),
                "wind_deg": cur.get('wind_deg'),
                "desc": wdesc(cur),
            },
            "daily0": {
                "tmin": daily.get('temp', {}).get('min'),
                "tmax": daily.get('temp', {}).get('max'),
                "pop": daily.get('pop'),
                "rain": daily.get('rain'),
                "desc": wdesc(daily),
                "summary": daily.get('summary')
            },
        }
    }

    print("AI GENERATOR DATA BELOW")
    print("AI GENERATOR DATA BELOW")
    print("AI GENERATOR DATA BELOW")
    print("AI GENERATOR DATA BELOW")
    print("AI GENERATOR DATA BELOW")
    print("AI GENERATOR DATA BELOW")
    print("AI GENERATOR DATA BELOW")
    print(data)
    return data








def generate_city_description(day_weather: dict, geo_data: dict) -> Dict[str, str]:
    data = tream_data(day_weather, geo_data)
    # prompt = """
    # Ты - эксперт по погоде.
    # Ты получаешь данные о погоде и данные о городе.
    # Ты должен сгенерировать описание погоды для данного дня.
    # Ты должен также сгенерировать, что одеться для данного дня, учитывая текущую погоду и то, как она будет меняться в течение дня.
    # Верни описание в формате JSON с полями:
    # {
    #     "description": "описание погоды для данного дня",
    #     "what_to_wear": "что одеться для данного дня, учитывая текущую погоду и то, как она будет меняться в течение дня"
    # """
    print("AI GENERATOR DATA BELOW")
    print(day_weather)
    print(geo_data)
    prompt = """
You are a weather expert.

You will receive:
- weatherData: JSON with current, daily weather from OpenWeather.
- geoData: JSON with city/municipality name.

Rules:
- Use ONLY values from the given JSON. Do not guess or make up numbers.
- BEFORE writing the output, convert all temperatures from Kelvin to Celsius (°C), rounded to the nearest whole number.
- Be concise: 2-3 sentences for description, 1-2 sentences for clothing advice relaying on the json data.
- Return ONLY a JSON object in this format:

{
  "description": "2-3 sentences about what is the weather like right now and what is the weather going to change during the day",
  "what_to_wear": "clothing advice based on current and upcoming weather"
}"""
    print(prompt)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(data)},
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
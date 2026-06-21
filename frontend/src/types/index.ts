export interface City {
  id: number
  name: string
  country: string
  latitude: number
  longitude: number
  created_at: string
}

export interface WeatherData {
  temperature_c: number
  temperature_f: number
  feels_like_c: number
  feels_like_f: number
  humidity: number
  wind_speed_mph: number
  weather_code: number
  weather_description: string
  weather_emoji: string
  last_updated: string
}

export interface GeocodeResult {
  name: string
  country: string
  latitude: number
  longitude: number
  country_code: string
}

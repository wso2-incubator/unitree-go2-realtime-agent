from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Conference Mock API", version="1.0.0")

# This is a simple mock API for conference agenda and speakers. You can replace this with real data or a database as needed.

@app.get("/agenda")
def get_agenda():
	"""Get the static mock event agenda."""
	return [
		{
			"agenda_day": "Day 1",
			"date": "2025-09-08",
			"title": "WSO2Con Asia 2025 Opening Keynote",
			"category": "Keynote",
			"startTime": "09:00",
			"endTime": "10:00"
		},
		{
			"agenda_day": "Day 1",
			"date": "2025-09-08",
			"title": "API Management with WSO2",
			"category": "Technical Session",
			"startTime": "10:30",
			"endTime": "11:15"
		},
		{
			"agenda_day": "Day 1",
			"date": "2025-09-08",
			"title": "Choreo: The Future of Platformless Modernization",
			"category": "Product Demo",
			"startTime": "11:30",
			"endTime": "12:00"
		}
	]

@app.get("/speakers")
def get_speakers():
	"""Get the static mock speaker list."""
	return [
		{
			"name": "Sanjiva Weerawarana",
			"title": "Founder & CEO, WSO2",
			"summary": "Sanjiva is the founder and CEO of WSO2, a visionary in open-source middleware."
		},
		{
			"name": "Rania Khalaf",
			"title": "Chief AI Officer, WSO2",
			"summary": "Rania leads AI strategy and innovation at WSO2, driving the company's AI initiatives."
		}
	]

if __name__ == "__main__":
	print("\nStarting Conference Mock API on http://localhost:8000")
	print("Available endpoints:")
	print("  GET /agenda    - Get event agenda")
	print("  GET /speakers  - Get speaker information")
	uvicorn.run(app, host="0.0.0.0", port=5100)

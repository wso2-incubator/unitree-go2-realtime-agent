
# Mock event/conference API for testing/demo purposes
import asyncio

async def fetch_event_agenda() -> str:
	"""
	Return a static mock WSO2Con agenda for testing.
	"""
	await asyncio.sleep(0.1)  # Simulate async call
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

async def fetch_speaker_info() -> str:
	"""
	Return a static mock WSO2Con speaker list for testing.
	"""
	await asyncio.sleep(0.1)  # Simulate async call
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

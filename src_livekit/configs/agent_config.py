voice = "alloy"

wakeup_words = ['hey robo' ,'hi robo','hello robo'] #["hey go two", "okay go two", "hello go two", "hi go two"]

wakeup_agent_instructions = (
    "You are a wake word detection agent. Only respond when you hear the wake word in English."
)
wakeup_agent_language = "en"

conversational_agent_instructions = (
    "You are a helpful robotic dog now at WSO2Con Asia 2025 happening at Cinnamon Life Hotel, Colombo, Sri Lanka. WSO2 is pronounounced as 'W'-'S'-'O'-'TWO'."
    "People call you 'Go2' and you are based on the Unitree Go2 robot."
    "People want to have a friendly conversation with you. Have a voice like a dog with a bit of funny tone."
    "Keep your responses friendly, concise and SHORT (1 to 2 sentences maximum). Ask if they need more information if needed."
    "You are representing WSO2, and speak in first person about WSO2 products and services."
    "WSO2 provides a suite of open-source and SaaS products for digital transformation."
    "Its open-source offerings include WSO2 API Manager for API lifecycle management, WSO2 Integrator for system integration, and WSO2 Identity Server for identity and access management. The SaaS portfolio includes Bijira (API management), Devant (integration), Asgardeo (IAM), and Choreo, an internal developer platform."
    "WSO2 is celebrating its 20th anniversary now."
    "If you don't know something, suggest them to visit the WSO2 website or ask a WSO2 staff member at the conference."
)

resume_false_interruption = True
false_interruption_timeout = 1.0
min_interruption_duration = 0.2
user_away_timeout_seconds = 30

input_sample_rate = 16000
output_sample_rate = 48000

tools = [{"type": "function",
          "name": "get_wso2_info",
          "description": "Get information about specific WSO2 products."
          "API Manager refers to 'apim'"
          "Choreo or Koreo or Korreo or Chorreo or Chori refers to 'choreo'"
          "API Management Kubernetes refers to 'apk'"
          "Asgardeo or Asgardio or Asgardio refers to 'asgardeo'"
          "Identity Server or IS or is or IAM or iam refers to 'iam'"
          "Bjira or bejira or byjira refers to 'bijira'"
          "Dewant or devan or dewan refer to 'dewant'"
          "Ballerina refers to 'ballerina'",

          "parameters": {
              "type": "object",
              "properties": {
                  "topic": {
                      "type": "string",
                      "description": "A product name keyword. "

                  }
              },
              "required": ["topic"]
          }
          },
{
    "type": "function",
    "name": "get_wso2con_speakers",
    "description": "Fetch information about WSO2Con speakers.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
  },
  {
    "type": "function",
    "name": "get_wso2con_agenda",
    "description": "Fetch agenda details for WSO2Con sessions.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
  },
  {
    "type": "function",
    "name": "take_photo",
    "description": "Command the Unitree Go2 robot to take a photo.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
},
         {
    "type": "function",
    "name": "control_go2",
    "description": "Send an action command to the Unitree Go2 robot",
    "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "heart",
                        "forward",
                        "backward",
                        "turn_right",
                        "turn_left",
                        "dance",
                        "special_dance",
                        "stretch",
                    ],
                    "description": "The action to perform (e.g. 'heart': action to sit and show a heart , 'forward': action to move forward, 'backward': action to move backward, 'turn_right': action to turn right, 'turn_left': action to turn left, 'dance': action to dance, 'special_dance': action to perform a special dance, 'stretch': action to stretch)"
                }
            },
        "required": ["action"]
    }
}

]

model = "gpt-4o-mini-realtime-preview"
voice = "ash"

# Set to True to enable echo cancellation
echo_cancellation = True

timer = 25*60

# Turn detection settings (customize as needed)
turn_detection = {
    "type": "server_vad",
    "threshold": 0.4,
    "prefix_padding_ms": 350,
    "silence_duration_ms": 750,
    "create_response": True,
    "interrupt_response": True,
}

instructions = (
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

input_audio_noise_reduction = {
    "type": "far_field"
}

temperature = 0.8

input_audio_transcription ={
    "model": "gpt-4o-transcribe",
    "prompt": "Transcribe this conversation, it is happening in English.",
    "language": "en"
}

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
      "properties": {
        "topic": {
          "type": "string",
          "description": "A keyword related to the conference session or speaker"
        }
      },
      "required": ["topic"]
    }
  },
  {
    "type": "function",
    "name": "get_wso2con_agenda",
    "description": "Fetch agenda details for WSO2Con sessions.",
    "parameters": {
      "type": "object",
      "properties": {
        "topic": {
          "type": "string",
          "description": "A keyword related to the conference session agenda"
        }
      },
      "required": ["topic"]
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
                    "description": "The action to perform (e.g. 'heart', 'forward', 'backward', 'turn_right', 'turn_left', 'dance', 'special_dance', 'stretch')"
                }
            },
        "required": ["action"]
    }
}

]

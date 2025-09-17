import os
from flask import Flask, request, jsonify
import sys
import time
import threading
import datetime
import dotenv
import logging

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient
from unitree_sdk2py.go2.video.video_client import VideoClient

dotenv.load_dotenv(override=True)
flask_port = os.getenv("FLASK_PORT", 5051)

# Create a lock to prevent concurrent /move and /action accesses
operation_lock = threading.Lock()
movement_lock = threading.Lock()

# Initialize Flask
app = Flask(__name__)

# Init SDK
if len(sys.argv) < 2:
    print(f"Usage: python3 {sys.argv[0]} <network_interface>")
    print("Example Default Mode: python3 control_service.py eth0")
    print("Example Test Mode: python3 control_service.py test")
    sys.exit(1)

if len(sys.argv) > 1:
    network_interface = sys.argv[1]

# Configure logging
logging.basicConfig(
    filename="flask_server-debug.log",
    filemode='w',  # Overwrites the log file each run
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

if network_interface == "test":
    class MockSportClient:
        def SetTimeout(self, timeout): pass
        def Init(self): pass
        def Move(self, vx, vy, yaw): return "mock_move"
        def StandUp(self): return "mock_standup"
        def StandDown(self): return "mock_standdown"
        def Stretch(self): return "mock_stretch"
        def Hello(self): return "mock_hello"
        def Heart(self): return "mock_heart"
        def Dance1(self): return "mock_dance1"
        def Dance2(self): return "mock_dance2"
        def StopMove(self): return "mock_stopmove"
        def Sit(self): return 0
        def RiseSit(self): return 0

    class MockVideoClient:
        def SetTimeout(self, timeout): pass
        def Init(self): pass
        def GetImageSample(self): return 0, b"mock_image_data"

    sport_client = MockSportClient()
else:
    ChannelFactoryInitialize(0, network_interface)
    sport_client = SportClient()
    sport_client.SetTimeout(10.0)
    sport_client.Init()


@app.route('/take_photo', methods=['POST'])
def capture_and_upload_photo():
    movement_lock.acquire()
    if not operation_lock.acquire(blocking=False):
        return jsonify({"error": "Robot is busy"}), 423  # 423 Locked
    try:
        if network_interface == "test":
            video_client = MockVideoClient()
            video_client.SetTimeout(3.0)
            video_client.Init()
            time.sleep(2)  # Simulate delay
            return jsonify({
                "status": "Test mode: Image captured successfully.",
            }), 200

        else:
            # Initialize Video Client
            video_client = VideoClient()
            video_client.SetTimeout(3.0)
            video_client.Init()

        # # Sit the robot before capturing an image
        now_time = datetime.datetime.now()
        sit_code = sport_client.Sit()
        if sit_code != 0:
            return jsonify({"error": f"Failed to sit the robot, code: {sit_code}"}), 500
        diff = int((datetime.datetime.now() - now_time).total_seconds())
        if diff < 3:
            time.sleep(3 - diff)
        # Wait for the robot to sit down
        # Capture image from robot

        now_time = datetime.datetime.now()
        code, data = video_client.GetImageSample()

        diff = int((datetime.datetime.now() - now_time).total_seconds())
        if diff < 3:
            time.sleep(3 - diff)

        if code != 0 or not data:
            return jsonify({"error": f"Failed to capture image, code: {code}"}), 500

        image_path = "./uploads/img.jpg"
        with open(image_path, "wb") as f:
            f.write(bytes(data))

        # Get back up
        sit_code = sport_client.RiseSit()
        if sit_code != 0:
            return jsonify({"error": f"Failed to rise the robot, code: {sit_code}"}), 500
        time.sleep(3)  # Wait for the robot to get back up

        return jsonify({
            "status": "Your image has been captured successfully. Check it out.",
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        operation_lock.release()
        movement_lock.release()

# Route: /move
@app.route('/move', methods=['POST'])
def move():
    # Priority check: don't move if another operation is ongoing
    if operation_lock.locked():
        logging.info("Move command blocked due to ongoing operation")
        return jsonify({"error": "Robot is busy"}), 423
    # Then acquire movement lock to ensure no concurrent /move commands
    if not movement_lock.acquire(blocking=False):
        logging.info("Move command blocked due to ongoing movement")
        return jsonify({"error": "Robot is busy"}), 423
    try:         
        data = request.json

        vx = float(data.get("vx", 0))
        vy = float(data.get("vy", 0))
        yaw = float(data.get("yaw", 0))

        if not (-2.5 <= vx <= 3.8):
            return jsonify({"error": "x_val must be between -2.5 and 3.8"}), 400
        if not (-1.0 <= vy <= 1.0):
            return jsonify({"error": "y_val must be between -1.0 and 1.0"}), 400
        if not (-4.0 <= yaw <= 4.0):
            return jsonify({"error": "yaw_val must be between -4.0 and 4.0"}), 400
        #execture a stop movement before executing any action
        code = sport_client.StopMove()
        time.sleep(1)  # Give some time for the robot to stop
        code = sport_client.Move(vx, vy, yaw)
        time.sleep(3)
        #log
        logger.info(f"Move command sent: vx={vx}, vy={vy}, yaw={yaw}, code={code}")
        return jsonify({"status": "ok", "code": code}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        logging.info("Releasing movement lock after move command")
        movement_lock.release()

# Route: /action/<action_name>
@app.route('/action/<action_name>', methods=['POST'])
def action(action_name):

    if not operation_lock.acquire(blocking=False):
        return jsonify({"error": "Robot is busy"}), 423  # 423 Locked
    try:
        api_timeout = 4
        #execture a stop movement before executing any action
        code = sport_client.StopMove()
        time.sleep(1)  # Give some time for the robot to stop
        # Map action names to actual SportClient methods
        if action_name.lower() == "forward":
            start_time = datetime.datetime.now()
            code = sport_client.Move(0.6, 0.0, 0.0)
            diff = int((datetime.datetime.now() - start_time).total_seconds())
        elif action_name.lower() == "backward":
            start_time = datetime.datetime.now()
            code = sport_client.Move(-0.6, 0.0, 0.0)
            diff = int((datetime.datetime.now() - start_time).total_seconds())
        elif action_name.lower() == "turn_left":
            start_time = datetime.datetime.now()
            code = sport_client.Move(0.0, 0.0, 1)
            diff = int((datetime.datetime.now() - start_time).total_seconds())
        elif action_name.lower() == "turn_right":
            start_time = datetime.datetime.now()
            code = sport_client.Move(0.0, 0.0, -1)
            diff = int((datetime.datetime.now() - start_time).total_seconds())
        else:
            action_map = {
                "get_up": sport_client.StandUp,
                "lie_down": sport_client.StandDown,
                "stretch": sport_client.Stretch,
                "hand_shake": sport_client.Hello,
                "heart": sport_client.Heart,
                "dance": sport_client.Dance1,
                "special_dance": sport_client.Dance2,
                "stop_movement": sport_client.StopMove,
                "sit_down": sport_client.Sit,
                "rise_from_sit_down": sport_client.RiseSit,
            }
            if action_name == "dance":
                api_timeout = 25
            elif action_name == "special_dance":
                api_timeout = 35
            elif action_name == "lie_down":
                api_timeout = 6
            elif action_name == "heart":
                api_timeout = 7
            elif action_name == "lie_down":
                api_timeout = 10
            elif action_name == "sit_down":
                api_timeout = 8
            elif action_name == "rise_from_sit_down":
                api_timeout = 8

            action_func = action_map.get(action_name.lower())

            if action_func is None:
                return jsonify({"error": f"Unsupported action: {action_name}"}), 400
            start_time = datetime.datetime.now()
            print(start_time)
            code = action_func()
            diff = int((datetime.datetime.now() - start_time).total_seconds())
        if api_timeout > diff:
            time.sleep(api_timeout - diff)
        logging.info(f"Action {action_name} executed with code: {code}")
        return jsonify({"status": f"{action_name} done for you.", "code": code}), 200

    except Exception as e:
        print(f"Error executing action {action_name}: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        logging.info(f"Releasing operation lock after action {action_name}")
        operation_lock.release()


# Start the Flask server
if __name__ == "__main__":
    #run the app and exit properly
    try:
        logging.info(f"Starting Unitree Go2 Control Service on port {FLASK_PORT}")
        app.run(host='0.0.0.0', port=FLASK_PORT, debug=True, use_reloader=True)
    
    except Exception as e:
        logging.exception(f"Flask server crashed with exception: {e}")
        sys.exit(1)
    finally:
        logging.info("Flask server stopped")

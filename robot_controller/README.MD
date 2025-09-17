## Setup (Run as separate terminal)

### 1. Install the Unitree SDK
If you encounter issues, refer to the [Unitree SDK website](https://github.com/unitreerobotics/unitree_sdk2_python).

```bash
cd robot_controller
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python
python -m venv .venv
source .venv/bin/activate
pip3 install -e .
cd ..
```

### 2. Install requirements

```bash
pip3 install -r requirements.txt
```


### 3. Start the Flask SDK Server

```bash
python3 control_service.py <network_interface>
# Example: python3 control_service.py eth0
# Or for test mode: python3 control_service.py test
```

### FAQ
**Q1: Error when running `pip3 install -e .`:**
```
Could not locate cyclonedds. Try to set CYCLONEDDS_HOME or CMAKE_PREFIX_PATH
```
This error means the cyclonedds path could not be found. First, compile and install cyclonedds:

```bash
cd ~
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x 
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install
```

Then, set `CYCLONEDDS_HOME` and install the SDK:

```bash
cd ~/unitree_sdk2_python
export CYCLONEDDS_HOME="~/cyclonedds/install"
pip3 install -e .
```

## Usage Examples

### Test Move
```bash
curl --location 'localhost:5051/move' \
    --header 'Content-Type: application/json' \
    --data '{
        "vx": 0,
        "vy": 1,
        "yaw": 1
    }'
```

### Test Action
```bash
curl --location 'localhost:5051/action/hand_shake' \
    --header 'Content-Type: application/json' \
    --data '{
        "vx": 0,
        "vy": 1,
        "yaw": 1
    }'
```

### Test Taking Photo

Open in browser or use curl:
```bash
POST localhost:5051/take_photo
```

The captured image will be saved to `uploads/img.jpg`.

---


For more details, see the code and comments in `control_service.py`.
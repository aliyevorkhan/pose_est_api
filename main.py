import requests
import base64
import sys

context = {
    "data": base64.b64encode(open(sys.argv[1], 'rb').read()),
    "hand_pose": 1,
    "which_hand": 0,

}

r = requests.post('http://127.0.0.1:8000/estimate/', json=context)

if r.status_code == 200:
    answer = str(input('Do you want to save response image? [y/N]: '))
    if answer.lower()=='y':
        print("image saved as response.jpg")
        open('response.jpg', 'wb').write(base64.b64decode(r.json()))
    else:
        print('successfully responsed:', r.status_code)
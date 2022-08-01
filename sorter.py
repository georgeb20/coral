#7/31/2022
from numpy import interp
from periphery import GPIO
import utils
from PIL import Image
import cv2
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from pycoral.adapters import common
from pycoral.adapters import classify
from scipy import ndimage

sendPin = 13
solenoid = GPIO("/dev/gpiochip2", sendPin, "out")  # pin 37
# Path to edgetpu compatible model

# the TFLite converted to be used with edgetpu
modelPath = 'mobilenet_v2_1.0_224_quant_edgetpu.tflite'

# The path to labels.txt that was downloaded with your model
labelPath = 'lucky_charm_labels.txt'




# this is the logic that determines if there is a sorting target in the center of the frame
def is_good_photo(img, width, height, mean, sliding_window):
    threshold = 4.5
    center = ndimage.measurements.center_of_mass(img)
    detection_zone_avg = (center[0] + center[1]) / 2


    if len(sliding_window) > 30:
        mean[0] = utils.mean_arr(sliding_window)
        sliding_window.clear()

    else:
        sliding_window.append(detection_zone_avg)
    # print(detection_zone_avg)
    if mean[0] != None and abs(detection_zone_avg - mean[0]) > threshold:
        print("Target Detected Taking Picture")
        return True

    return False

# call each time you  have a new frame
def on_new_frame(cv_mat, interpreter, mean, sliding_window):
    img_pil = Image.fromarray(cv_mat)

    width, height = img_pil.size

    is_good_frame = is_good_photo(cv_mat, width, height, mean, sliding_window)
    if (is_good_frame):
        size = common.input_size(interpreter)
        common.set_input(interpreter, cv2.resize(cv_mat, size, fx=0, fy=0,
                                                interpolation=cv2.INTER_CUBIC))
        interpreter.invoke()
        results = classify.get_classes(interpreter)
        if labels[results[0].id] == 'charm' and  results[0].score > 0.95:
            solenoid.write(True)
        else:
            solenoid.write(False)
        # Here you can actuate the sorting end-effector through GPIO, etc.


if __name__ == '__main__':
    interpreter = make_interpreter(modelPath)
    interpreter.allocate_tensors()
    labels = read_label_file(labelPath)

    mean = [None]
    sliding_window = []


    cap = cv2.VideoCapture(1)
    while cap.isOpened():
        ret,frame = cap.read()
        # Flip image so it matches the training input
        #frame = cv2.flip(frame, 1)
        if  not ret:
            break
        on_new_frame(cv_mat=frame,interpreter=interpreter, mean=mean, sliding_window=sliding_window)
        if cv2.waitKey(1) & 0xff  == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    print('Initializing opencv Video Stream')

#7/31/2022
from periphery import GPIO
import cv2
import utils
from PIL import Image
import edgetpu.classification.engine

sendPin = 13
solenoid = GPIO("/dev/gpiochip2", sendPin, "out")  # pin 37
# Path to edgetpu compatible model
model_path = '../model_edgetpu.tflite'





# this is the logic that determines if there is a sorting target in the center of the frame
def is_good_photo(img, width, height, mean, sliding_window):
    detection_zone_height = 20
    detection_zone_interval = 5
    threshold = 4.5
    detection_zone_avg = img[height // 2 : (height // 2) + detection_zone_height : detection_zone_interval, 0:-1:3].mean()



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
def on_new_frame(cv_mat, engine, mean, sliding_window):
    img_pil = Image.fromarray(cv_mat)

    width, height = img_pil.size

    is_good_frame = is_good_photo(cv_mat, width, height, mean, sliding_window)
    if (is_good_frame):

        if (width, height) != (224, 224):
            img_pil.resize((224, 224))

            classification_result = engine.ClassifyWithImage(img_pil)
            print(classification_result)
            if classification_result [0][0] == 0 and  classification_result[0][1] > 0.95:
                solenoid.write(True)
            else:
                solenoid.write(False)
            # Here you can actuate the sorting end-effector through GPIO, etc.


if __name__ == '__main__':



    engine = edgetpu.classification.engine.ClassificationEngine(model_path)
    mean = [None]
    sliding_window = []


    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret,frame = cap.read()
        if  not ret:
            break
        on_new_frame(cv_mat=frame,engine=engine, mean=mean, sliding_window=sliding_window)
        if cv2.waitKey(1) & 0xff  == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    print('Initializing opencv Video Stream')

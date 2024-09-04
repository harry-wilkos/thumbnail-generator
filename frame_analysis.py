from process import thread, retrieve
import os
from pathlib import PurePath
import glob
import gc
import json
from sys import argv
from bson.objectid import ObjectId
os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
if "ffmpeg" not in os.environ.get("PATH"):
    raise Exception("ffmpeg must be installed to analyse video")
try:
    import cv2
    import clique
    import ffmpegcv
    import PyOpenColorIO as OCIO
    from pymongo import MongoClient
except ImportError:
    import pip, site
    from importlib import reload
    pip.main(["install", "opencv-contrib-python", "-q"])
    pip.main(["install", "clique", "-q"])
    pip.main(["install", "ffmpegcv", "-q"])
    pip.main(["install", "opencolorio", "-q"])
    pip.main(["install", "pymongo", "-q"])
    reload(site)
    import cv2
    import clique
    import ffmpegcv
    import PyOpenColorIO as OCIO
    from pymongo import MongoClient
import numpy as np

def get_quality(frame_cap, quality, num_frames):

    # Set no frame_cap
    if frame_cap <= 0:
        frame_cap = num_frames

    # Create frame incrememnt value
    target_quality = round(num_frames * quality)
    increment = num_frames / min(frame_cap, target_quality)

    # Correct broken values
    if increment > num_frames:
        increment = num_frames

    # Create frame numbers to process
    step = 0
    a_frames =[0]
    while step < num_frames - 1:
        step += increment
        rounded = round(step)
        if rounded <= num_frames - 1:
            a_frames.append(rounded)
    
    #Create single quaity value for database
    store_quality = len(a_frames)/num_frames
    return a_frames, store_quality, num_frames

    

def get_paths(input, store_quality):

    path = PurePath(input)
    
    fps = False
    exr = False
    a_frames, store_quality, num_frames = store_quality

    if len(path.suffixes) == 1:
        vid = ffmpegcv.noblock(ffmpegcv.VideoCapture, input)
        if num_frames is None:
            num_frames = vid.count
            a_frames, store_quality, num_frames = get_quality(a_frames, store_quality, num_frames)
        fps = round(vid.fps)

        run = True
        files = []
        while run:
            run, img = vid.read()
            if not run:
                break
            files.append(img.copy())

        vid.release()
        frame_list = list(range(1, num_frames + 1))
    else:
        pattern = path.name.split(".")[0] + "*" + path.suffix 
        files = glob.glob(str(PurePath(path.parent / pattern)))
        assembly = clique.assemble(files)[0][0]
        frame_list = assembly.indexes
        if assembly.tail == ".exr": 
            exr = True
        if num_frames is None:
            num_frames = len(frame_list)
            a_frames, store_quality, num_frames = get_quality(a_frames, store_quality, num_frames)
        


    frame_paths = []
    for f, frame in enumerate(frame_list):

        # Frames to ignore
        if len(a_frames) == 0:
            check = False 
        elif f != a_frames[0]:
            check = False

        else:
            # Pixel arrays from video
            if fps:
                check = files[frame - 1]

            # File paths from sequence
            else:
                check = assembly.head + str(frame).zfill(assembly.padding) + assembly.tail
            a_frames.pop(0)

        frame_paths.append([check, fps, exr])

   
    return frame_paths, num_frames, fps, store_quality

def aces_srgb(read):

    # Get available colour spaces
    config = OCIO.Config.CreateFromEnv()
    if not config.getName():
        config = OCIO.Config.CreateFromBuiltinConfig("ocio://cg-config-v2.1.0_aces-v1.3_ocio-v2.3")

    aces = None
    srgb = None
    cs = config.getColorSpaceNames()
    for color in cs:
        if "ACEScg" in color and not aces:
            aces = color
        elif "Rec.709" in color and not srgb:
            srgb = color
        if aces and srgb:
            break

    if not aces or not srgb:
        raise ValueError("Could not find the appropriate color spaces in the OCIO configuration")

    if read.dtype != np.float32:
        read = read.astype(np.float32)

    # Remove alpha
    if read.shape[2] == 4:
        read = read[:, :, :3]  

    rgb = cv2.cvtColor(read, cv2.COLOR_BGR2RGB)

    # Convert to rec 709
    processor_2 = config.getProcessor(aces, srgb)
    cpu_2 = processor_2.getDefaultCPUProcessor()
    cpu_2.applyRGB(rgb)

    # Adjust Gamma
    transform = OCIO.ExposureContrastTransform()
    transform.setStyle(OCIO.ExposureContrastStyle(2))
    transform.setExposure(1)

    # Apply Changes
    processor_1 = config.getProcessor(transform)
    cpu_1 = processor_1.getDefaultCPUProcessor()
    cpu_1.applyRGB(rgb)
    converted_rgb = np.clip(rgb, 0, 1)

    converted_rgb_8bit = cv2.cvtColor((converted_rgb * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)

    return converted_rgb_8bit

def fit(array, new_max):

    # normalise array values between 0 and 1
    old_min = min(array)
    old_max = max(array)
    n_array = []
    for a in array:
        if (old_max - old_min == 0):
            result = 0
        else:
            result = (((a - old_min) * new_max)/ (old_max - old_min))
        n_array.append(result)
    return n_array

def color_var(path, fps, exr):

    if path is False:
        return 0.0
    elif fps:
        image = path
    elif exr:
        image = cv2.imread(path, -1)
        image = aces_srgb(image)
    else:
        image = cv2.imread(path)

    # Convert to HSV
    HSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(HSV.astype("float"))

    # Standard deviation of the hue
    h_std = np.std(H)
    # 50th percentile of the saturation
    s_ndp = np.mean(S) + (0.5 * np.std(S))
    # 50th percentile of the value
    v_ndp = np.mean(V) + (0.5 * np.std(V))

    out = s_ndp * v_ndp * h_std
    # Correct for invalid values
    if out == 0.0:
        out = 1.0

    return out

def framing(path, fps, exr):

    if path is False:
        return 0.0
    elif fps:
        image = path
    elif exr:
        image = cv2.imread(path, -1)
        image = aces_srgb(image)
    else:
        image = cv2.imread(path)

    # Detect edges and make contours
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3,3), 0)
    edges = cv2.Canny(blurred, 0, 175)
    contours = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]

    # Create a rotated bounding box and calc area
    if len(contours) == 0:
        area = 1.0
    else:
        rect = cv2.minAreaRect(contours[0])
        area = rect[1][0] * rect[1][1]

    return area


def main(input, store_quality, color_weight, focus_weight, db_address, id):
    
    gc.collect()

    frame_paths, num_frames, fps, store_quality = get_paths(input, store_quality)


    # calculate colour variation and framing
    cv_threads = thread(color_var, frame_paths)
    f_threads = thread(framing, frame_paths)
    color_results, framing_results = retrieve(cv_threads, f_threads)

    # Implement custom score ratio
    if color_weight == -1:
        normalised_color = color_results
    else:
        normalised_color = fit(color_results,color_weight)

    if focus_weight == -1:
        normalised_framing = framing_results
    else:
        normalised_framing = fit(framing_results,focus_weight)

    # Get largest score
    score = [normalised_color[i] + normalised_framing[i] for i in range(num_frames)]
    index = score.index(max(score))

    # Get highest scoring frame
    if fps:
        output = round(index/fps, 2)
    else:
        output = (list(frame_paths)[index])[0]

    # Get Mongo DB

    collection = MongoClient(db_address[0]).get_database(db_address[1]).get_collection(db_address[2])

    collection.update_one({"_id": ObjectId(id)},{
        "$set":{
            "thumbnail": output,
            "quality": store_quality,
            "num_frames": num_frames,
            "processing": False
        }
    })


    return output
 
if __name__ == "__main__":
    main(**json.loads(argv[1]))

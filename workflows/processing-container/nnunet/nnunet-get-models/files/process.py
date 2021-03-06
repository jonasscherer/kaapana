import sys
import os
import urllib.request
import zipfile
import time
from datetime import datetime
from pathlib import Path


max_retries = 3
max_hours_since_creation = 3
models_dir = os.path.join(os.getenv('MODELDIR', "/models"), "nnUNet")
task_ids = os.getenv('TASK', None)
model = os.getenv('MODEL', None)

Path(models_dir).mkdir(parents=True, exist_ok=True)


def check_dl_running(model_path_dl_running, model_path, wait=True):
    if os.path.isfile(model_path_dl_running):
        hours_since_creation = int((datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path_dl_running))).total_seconds()/3600)
        if hours_since_creation > max_hours_since_creation:
            print("Download lock-file present! -> waiting until it is finished!")
            print("File older than {} hours! -> removing and triggering download!".format(max_hours_since_creation))
            delete_file(model_path_dl_running)
            return False    

        print("Download already running -> waiting until it is finished!")
        while not os.path.isdir(model_path) and wait:
            time.sleep(15)
        return True
    else:
        print("Download not running -> download!")
        return False


def delete_file(target_file):
    try:
        os.remove(target_file)
    except Exception as e:
        print(e)
        pass


if task_ids is None:
    print("No ENV 'TASK' found!")
    print("Abort.")
    exit(1)

if model is None:
    model = "2d"

if task_ids == "all":
    print("Downloading all nnUnet-task-models...")
    task_ids = [
        # "Task001_BrainTumour",
        "Task002_Heart",
        "Task003_Liver",
        "Task004_Hippocampus",
        # "Task005_Prostate",
        "Task006_Lung",
        "Task007_Pancreas",
        "Task008_HepaticVessel",
        "Task009_Spleen",
        "Task010_Colon",
        "Task017_AbdominalOrganSegmentation",
        "Task024_Promise",
        "Task027_ACDC",
        "Task029_LITS",
        # "Task035_ISBILesionSegmentation",
        # "Task038_CHAOS_Task_3_5_Variant2",
        "Task048_KiTS_clean",
        "Task055_SegTHOR",
        # "Task061_CREMI",
        # "Task075_Fluo_C3DH_A549_ManAndSim",
        # "Task076_Fluo_N3DH_SIM",
        # "Task089_Fluo-N2DH-SIM_thickborder_time"
    ]
else:
    task_ids = [task_ids]

for task_id in task_ids:
    model_path = os.path.join(models_dir, model, task_id)
    print("Check if model already present: {}".format(model_path))
    print("TASK: {}".format(task_id))
    print("MODEL: {}".format(model))
    if os.path.isdir(model_path):
        print("Model {} found!".format(task_id))
        continue

    print("Model not present: {}".format(model_path))

    model_path_dl_running = os.path.join(models_dir, "dl_{}.txt".format(task_id))
    wait = True if len(task_ids) == 1 else False
    if check_dl_running(model_path_dl_running=model_path_dl_running, model_path=model_path, wait=wait):
        continue

    file_name = "{}.zip".format(task_id)
    model_url = "https://zenodo.org/record/4003545/files/{}?download=1".format(file_name)

    output_dir = os.path.join('/', os.getenv("WORKFLOW_DIR", "tmp"), os.getenv("OPERATOR_OUT_DIR", ""))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try_count = 0
    target_file = os.path.join(output_dir, file_name)
    while not os.path.isfile(target_file) and try_count < max_retries:
        print("Try: {} - Start download: {}".format(try_count, model_url))
        try_count += 1
        try:
            Path(model_path_dl_running).touch()
            urllib.request.urlretrieve(model_url, target_file)
        except Exception as e:
            print("Could not download model: {}".format(model_url))
            print("Abort.")
            print('MSG: ' + str(e))
            delete_file(target_file)

    if try_count >= max_retries:
        print("------------------------------------")
        print("Max retries reached!")
        print("Skipping...")
        print("------------------------------------")
        delete_file(model_path_dl_running)
        continue

    print("------------------------------------")
    print("Task-model zip-file found!")
    print("------------------------------------")
    print("Start extraction: {}".format(target_file))
    print("------------------------------------")
    print("Target-dir: {}".format(models_dir))
    print("------------------------------------")

    try:
        with zipfile.ZipFile(target_file, "r") as zip_ref:
            zip_ref.extractall(models_dir)
    except Exception as e:
        print("Could not extract model: {}".format(zipfile))
        print("Target dir: {}".format(models_dir))
        print("Abort.")
        print('MSG: ' + str(e))
        delete_file(target_file)
        delete_file(model_path_dl_running)
        continue

    delete_file(model_path_dl_running)

print("------------------------------------")
print("------------------------------------")
print("Check if all models are now present: {}".format(model_path))
print("------------------------------------")
for task_id in task_ids:
    model_path = os.path.join(models_dir, model, task_id)
    if os.path.isdir(model_path):
        print("Model {} found!".format(task_id))
        print("------------------------------------")
        continue
    else:
        print("------------------------------------")
        print("------------------------------------")
        print("------------   ERROR!  -------------")
        print("------------------------------------")
        print("Model NOT found: {}".format(models_dir))
        print("------------------------------------")
        print("------------------------------------")
        exit(1)

print("All models successfully downloaded and extracted!")
print("DONE")
exit(0)

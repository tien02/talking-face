import os
import sys
from pathlib import Path
import shutil
import time
import torch
from time import strftime

from src.sadtalker.utils.preprocess import CropAndExtract
from src.sadtalker.test_audio2coeff import Audio2Coeff
from src.sadtalker.generate_batch import get_data
from src.sadtalker.generate_facerender_batch import get_facerender_data
from src.sadtalker.utils.init_path import init_path
from schemas.video import SadTalkerAnimatorInput, SadTalkerAnimatorResponse
from config.video import video_settings

class SadTalkerAnimator:
    def __init__(self, batch_size=video_settings.VIDEO_BATCH_SIZE, enhancer=None,
                 checkpoint_dir='./checkpoints', result_dir='./results', device=video_settings.VIDEO_DEVICE,
                 size=256, preprocess='full', old_version=False, background_enhancer=None,
                 pose_style=0, expression_scale=1.0, still=True, face3dvis=False,
                 input_yaw=None, input_pitch=None, input_roll=None, verbose=False,
                 ref_eyeblink=None, ref_pose=None, use_trt=video_settings.USE_VIDEO_TRT_MODEL):
        
        self.batch_size = batch_size
        self.enhancer = enhancer
        self.checkpoint_dir = checkpoint_dir
        self.result_dir = result_dir
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.size = size
        self.pose_style = pose_style
        self.expression_scale = expression_scale
        self.still = still
        self.face3dvis = face3dvis
        self.input_yaw = input_yaw
        self.input_pitch = input_pitch
        self.input_roll = input_roll
        self.preprocess = preprocess
        self.old_version = old_version
        self.verbose = verbose
        self.background_enhancer = background_enhancer
        self.ref_eyeblink = ref_eyeblink
        self.ref_pose = ref_pose
        self.use_trt = use_trt

        # current_root_path = os.path.split(sys.argv[0])[0]
        current_root_path = Path(__file__).resolve().parents[1]
        config_path = current_root_path / 'src' / 'sadtalker' / 'config'
        self.sadtalker_paths = init_path(self.checkpoint_dir, str(config_path), self.size, self.old_version, self.preprocess)

        self.preprocess_model = CropAndExtract(self.sadtalker_paths, self.device)
        self.audio_to_coeff = Audio2Coeff(self.sadtalker_paths, self.device)

        if self.use_trt:
            from src.sadtalker.facerender.animate_trt import AnimateFromCoeff
        else:
            from src.sadtalker.facerender.animate import AnimateFromCoeff
        self.animate_from_coeff = AnimateFromCoeff(self.sadtalker_paths, self.device)

    def __call__(self, inp:SadTalkerAnimatorInput) -> SadTalkerAnimatorResponse:
        driven_audio = inp.driven_audio
        source_image = inp.source_image

        save_dir = os.path.join(self.result_dir, strftime("%Y_%m_%d_%H.%M.%S"))
        os.makedirs(save_dir, exist_ok=True)

        first_frame_dir = os.path.join(save_dir, 'first_frame_dir')
        os.makedirs(first_frame_dir, exist_ok=True)
        print('3DMM Extraction for source image')
        first_coeff_path, crop_pic_path, crop_info = self.preprocess_model.generate(
            source_image, first_frame_dir, self.preprocess, source_image_flag=True, pic_size=self.size)

        if first_coeff_path is None:
            print("Can't get the coeffs of the input")
            return

        ref_eyeblink_coeff_path = None
        if self.ref_eyeblink:
            ref_eyeblink_name = os.path.splitext(os.path.basename(self.ref_eyeblink))[0]
            ref_eyeblink_dir = os.path.join(save_dir, ref_eyeblink_name)
            os.makedirs(ref_eyeblink_dir, exist_ok=True)
            print('3DMM Extraction for the reference video providing eye blinking')
            ref_eyeblink_coeff_path, _, _ = self.preprocess_model.generate(
                self.ref_eyeblink, ref_eyeblink_dir, self.preprocess, source_image_flag=False)

        ref_pose_coeff_path = None
        if self.ref_pose:
            if self.ref_pose == self.ref_eyeblink:
                ref_pose_coeff_path = ref_eyeblink_coeff_path
            else:
                ref_pose_name = os.path.splitext(os.path.basename(self.ref_pose))[0]
                ref_pose_dir = os.path.join(save_dir, ref_pose_name)
                os.makedirs(ref_pose_dir, exist_ok=True)
                print('3DMM Extraction for the reference video providing pose')
                ref_pose_coeff_path, _, _ = self.preprocess_model.generate(
                    self.ref_pose, ref_pose_dir, self.preprocess, source_image_flag=False)

        start = time.time()

        batch = get_data(first_coeff_path, driven_audio, self.device, ref_eyeblink_coeff_path, still=self.still)
        coeff_path = self.audio_to_coeff.generate(batch, save_dir, self.pose_style, ref_pose_coeff_path)

        if self.face3dvis:
            from src.sadtalker.face3d.visualize import gen_composed_video
            gen_composed_video(self, self.device, first_coeff_path, coeff_path, driven_audio,
                               os.path.join(save_dir, '3dface.mp4'))

        data = get_facerender_data(coeff_path, crop_pic_path, first_coeff_path, driven_audio,
                                   self.batch_size, self.input_yaw, self.input_pitch, self.input_roll,
                                   expression_scale=self.expression_scale, still_mode=self.still,
                                   preprocess=self.preprocess, size=self.size)

        result = self.animate_from_coeff.generate(data, save_dir, source_image, crop_info,
                                                  enhancer=self.enhancer,
                                                  background_enhancer=self.background_enhancer,
                                                  preprocess=self.preprocess, img_size=self.size)

        end = time.time()

        total_time = end-start
        output_video = save_dir + '.mp4'
        shutil.move(result, output_video)

        if not self.verbose:
            shutil.rmtree(save_dir)

        return SadTalkerAnimatorResponse(
            output_video=output_video,
            total_time=total_time
        )

if __name__ == "__main__":
    animator = SadTalkerAnimator(batch_size=2)
    output_video = animator(
        driven_audio="./examples/audio.wav",
        source_image="./examples/avatar.png",
    )

    print(output_video)

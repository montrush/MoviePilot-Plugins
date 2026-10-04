import json
import os
import subprocess


class Ffmpeg:

    @staticmethod
    def extract_wav_from_video(video_path, audio_path, audio_index=None):
        """
        使用ffmpeg从视频文件中提取16000hz, 16-bit的wav格式音频
        """
        if not video_path or not audio_path:
            return False

        # 提取指定音频流
        if audio_index:
            command = ['ffmpeg', "-hide_banner", "-loglevel", "warning", '-y', '-i', video_path,
                       '-map', f'0:a:{audio_index}',
                       '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', audio_path]
        else:
            command = ['ffmpeg', "-hide_banner", "-loglevel", "warning", '-y', '-i', video_path,
                       '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', audio_path]

        ret = subprocess.run(command).returncode
        if ret == 0:
            return True
        return False

    @staticmethod
    def get_video_metadata(video_path):
        """
        获取视频元数据
        """
        if not video_path:
            return False

        try:
            command = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return json.loads(result.stdout.decode("utf-8"))
        except Exception as e:
            print(e)
        return None

    @staticmethod
    def extract_subtitle_from_video(video_path, subtitle_path, subtitle_index=None):
        """
        从视频中提取字幕
        PATCH(1001): 逐轨尝试并按>=2KB校验, 拒绝强制字幕空轨(如ATVP首条eng轨只有片头字幕)
        """
        if not video_path or not subtitle_path:
            return False

        candidates = []
        if subtitle_index is not None and subtitle_index != '':
            candidates.append(subtitle_index)
        try:
            probe = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_path],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            meta = json.loads(probe.stdout.decode("utf-8"))
            rel = 0
            for st in meta.get("streams", []):
                if st.get("codec_type") == "subtitle":
                    if str(rel) != str(subtitle_index):
                        candidates.append(rel)
                    rel += 1
        except Exception:
            pass

        for idx in candidates:
            try:
                os.path.exists(subtitle_path) and os.remove(subtitle_path)
            except Exception:
                pass
            command = ['ffmpeg', "-hide_banner", "-loglevel", "warning", '-y', '-i', video_path,
                       '-map', f'0:s:{idx}', subtitle_path]
            if subprocess.run(command).returncode != 0:
                continue
            try:
                if os.path.getsize(subtitle_path) >= 2048:
                    return True
            except Exception:
                pass
        return False

from enum import Enum


class ActionTypes(str, Enum):
    open_url = "openUrl"
    im_back = "imBack"
    post_back = "postBack"
    play_audio = "playAudio"
    play_video = "playVideo"
    show_image = "showImage"
    download_file = "downloadFile"
    signin = "signin"
    call = "call"
    message_back = "messageBack"
